"""Reserve on rate limits reported inside an OmniRoute stream; bounded waits; no replay after content."""
import http.client
import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import core
import gateway

IMAGE = {'google/gemma-4-31b-it:free', 'google/gemma-4-26b-a4b-it:free', 'nvidia/nemotron-3.5-super-vl:free'}
CHAIN = core.ROLES['router-coder']
CODER, CODER_RESERVE = CHAIN[:2]
VISUAL, VISUAL_RESERVE = core.ROLES['router-visual']
PING = b'event: ping\ndata: {"type":"ping"}\n\n'
# What OmniRoute 3.8.51 writes into its early 200 stream after every account answered 429.
RATE_LIMITED = (b'event: error\ndata: {"error":{"message":"[429]: model is temporarily rate-limited upstream",'
                b'"type":"rate_limit_error","code":"rate_limit_exceeded"}}\n\n')


def message(model):
    return ('event: message_start\ndata: {"type":"message_start","message":{"model":"' + model + '"}}\n\n'
            'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"reply from ' + model + '"}}\n\n'
            'event: message_stop\ndata: {"type":"message_stop"}\n\n').encode()


class FakeOmniRoute(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def stream(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        model = body['model'].removeprefix('openrouter/')
        self.server.seen.append(model)
        script = self.server.scripts.get(model, [])
        action = script.pop(0) if script else 'ok'
        if action == 'http504':
            data = b'{"error":{"message":"Gateway Timeout","type":"api_error"}}'
            self.send_response(504)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if action == 'http429':
            data = json.dumps({'error': {'message': 'Rate limit exceeded', 'type': 'rate_limit_error'}}).encode()
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Retry-After', '30')
            self.end_headers()
            self.wfile.write(data)
            return
        self.stream()
        if action == 'ok':
            self.wfile.write(PING + message(model))
        elif action == 'stream429':
            self.wfile.write(PING + PING + RATE_LIMITED)
        elif action == 'auth':
            self.wfile.write(PING + b'event: error\ndata: {"error":{"message":"Invalid API key provided","type":"authentication_error"}}\n\n')
        elif action == 'partial':
            self.wfile.write(message(model)[:80] + b'\n\n' + RATE_LIMITED)
        elif action == 'stall':
            # Keepalive pings only, as OmniRoute does while it cycles through rate-limited accounts.
            end = time.monotonic() + 10
            try:
                while time.monotonic() < end:
                    self.wfile.write(PING)
                    self.wfile.flush()
                    time.sleep(.05)
            except OSError:
                self.server.abandoned.append(model)


class Harness(unittest.TestCase):
    def setUp(self):
        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), FakeOmniRoute)
        self.upstream.seen, self.upstream.scripts, self.upstream.abandoned = [], {}, []
        threading.Thread(target=self.upstream.serve_forever, daemon=True).start()
        catalog = {m: {'free': True, 'tools': True, 'modalities': ['text', 'image'] if m in IMAGE else ['text'],
                       'context': 262144, 'max_output': 32768, 'expires': None} for m in core.MODELS}
        self.gate = gateway.Gateway('synthetic-local-key', catalog, f'http://127.0.0.1:{self.upstream.server_port}')
        threading.Thread(target=self.gate.serve_forever, daemon=True).start()

    def tearDown(self):
        self.gate.shutdown(); self.gate.server_close()
        self.upstream.shutdown(); self.upstream.server_close()

    def request(self, model='router-coder', content='fixture'):
        connection = http.client.HTTPConnection('127.0.0.1', self.gate.server_port, timeout=20)
        body = {'model': model, 'max_tokens': 10, 'stream': True, 'messages': [{'role': 'user', 'content': content}]}
        connection.request('POST', '/v1/messages', json.dumps(body), {'Authorization': 'Bearer ' + self.gate.token})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result


class ReserveTests(Harness):
    def test_rate_limit_inside_stream_uses_reserve(self):
        self.upstream.scripts[CODER] = ['stream429']
        status, headers, data = self.request()
        self.assertEqual(status, 200)
        self.assertIn(b'reply from ' + CODER_RESERVE.encode(), data)
        self.assertNotIn(b'rate_limit', data)  # the client never sees the principal's attempt
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE])
        self.assertEqual(headers['X-Claude-Perfis-Model'], CODER_RESERVE)
        self.assertIn((CODER, 'reserve-next', 429), [(e['model'], e['outcome'], e['status']) for e in self.gate.events])

    def test_http_429_uses_reserve_and_principal_is_skipped_while_cooling(self):
        self.upstream.scripts[CODER] = ['http429']
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE, CODER_RESERVE])

    def test_rate_limit_on_whole_chain_stops_and_reports_without_cycling(self):
        for model in CHAIN:
            self.upstream.scripts[model] = ['stream429']
        status, headers, data = self.request()
        self.assertEqual(status, 429)
        self.assertEqual(headers['x-should-retry'], 'false')
        self.assertGreaterEqual(int(headers['Retry-After']), 15)
        error = json.loads(data)['error']
        self.assertEqual(error['type'], 'rate_limit_error')
        for text in ('router-coder', *(core.MODEL_NAMES[m] for m in CHAIN), 'informe o usuario'):
            self.assertIn(text, error['message'])
        self.assertEqual(self.upstream.seen, list(CHAIN))
        # Attempt limit: while both models cool down, a new request fails at once without an upstream call.
        start = time.monotonic()
        status, headers, _ = self.request()
        self.assertEqual(status, 429)
        self.assertEqual(headers['x-should-retry'], 'false')
        self.assertLess(time.monotonic() - start, 2)
        self.assertEqual(self.upstream.seen, list(CHAIN))

    def test_stalled_principal_is_abandoned_at_the_deadline(self):
        self.gate.first_event_seconds = (.6, .6)
        self.upstream.scripts[CODER] = ['stall']
        start = time.monotonic()
        status, _, data = self.request()
        self.assertEqual(status, 200)
        self.assertLess(time.monotonic() - start, 5)
        self.assertIn(b'reply from ' + CODER_RESERVE.encode(), data)
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE])
        for _ in range(60):  # the stalled attempt is closed, not left running
            if self.upstream.abandoned:
                break
            time.sleep(.05)
        self.assertEqual(self.upstream.abandoned, [CODER])

    def test_stall_on_whole_chain_returns_timeout_instead_of_waiting(self):
        self.gate.first_event_seconds = (.4, .4)
        for model in CHAIN:
            self.upstream.scripts[model] = ['stall']
        start = time.monotonic()
        status, headers, data = self.request()
        self.assertEqual(status, 504)
        self.assertEqual(headers['x-should-retry'], 'false')
        self.assertLess(time.monotonic() - start, 5)
        self.assertIn('sem resposta dentro do prazo', json.loads(data)['error']['message'])

    def test_image_request_never_uses_a_text_only_reserve(self):
        image = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': 'AAAA'}}]
        self.upstream.scripts[CODER] = ['stream429']
        status, _, data = self.request('router-coder', image)
        self.assertEqual(status, 429)
        self.assertEqual(self.upstream.seen, [CODER])  # the rest of the coder chain has no image input
        self.assertNotIn(CODER_RESERVE, json.loads(data)['error']['message'])
        # The visual role's reserve accepts images, so it is used.
        self.upstream.scripts[VISUAL] = ['stream429']
        status, _, data = self.request('router-visual', image)
        self.assertEqual(status, 429)  # its reserve is the same model, still cooling
        self.assertEqual(self.upstream.seen, [CODER, VISUAL])
        self.gate.cooling.clear()
        self.upstream.scripts[VISUAL] = ['stream429']
        status, _, data = self.request('router-visual', image)
        self.assertEqual(status, 200)
        self.assertIn(b'reply from ' + VISUAL_RESERVE.encode(), data)

    def test_auth_error_inside_stream_never_tries_reserve(self):
        self.upstream.scripts[CODER] = ['auth']
        status, _, data = self.request()
        self.assertEqual(status, 200)
        self.assertIn(b'authentication_error', data)
        self.assertEqual(self.upstream.seen, [CODER])

    def test_error_after_content_is_never_replayed(self):
        self.upstream.scripts[CODER] = ['partial']
        status, _, data = self.request()
        self.assertEqual(status, 200)
        self.assertIn(b'message_start', data)
        self.assertEqual(self.upstream.seen, [CODER])
        self.assertFalse(self.gate.cooling)

    def test_principal_returns_after_cooldown(self):
        self.gate.cooldown_seconds = (.2, .2, .2)
        self.upstream.scripts[CODER] = ['stream429']
        self.assertEqual(self.request()[0], 200)
        time.sleep(.3)
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE, CODER])


class ChainTests(Harness):
    """router-coder chain: four providers, a failed model sits out, bounded total wait."""

    def test_coder_chain_spans_four_providers_with_xing_last(self):
        self.assertEqual(CHAIN, ('google/gemma-4-31b-it:free', 'cohere/north-mini-code:free',
                                 'nvidia/nemotron-3.5-lightning:free', 'xingchen-agi/xing4.0-29b-a4b:free'))
        self.assertEqual(len({model.split('/')[0] for model in CHAIN}), 4)
        for model in CHAIN[:3]:
            self.upstream.scripts[model] = ['stream429']
        status, headers, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(self.upstream.seen, list(CHAIN))
        self.assertEqual(headers['X-Claude-Perfis-Model'], CHAIN[3])

    def test_default_cooldown_is_five_minutes_and_retry_after_is_bounded(self):
        self.assertEqual(gateway.COOLDOWN_SECONDS, (15, 300, 900))
        self.gate.cool(CHAIN[0])
        self.assertAlmostEqual(self.gate.cooling_left(CHAIN[0]), 300, delta=2)
        self.gate.cool(CHAIN[1], 86400)
        self.assertAlmostEqual(self.gate.cooling_left(CHAIN[1]), 900, delta=2)
        self.gate.cool(CHAIN[2], 1)
        self.assertAlmostEqual(self.gate.cooling_left(CHAIN[2]), 15, delta=2)
        # A provider's Retry-After inside the bounds is used as given.
        self.upstream.scripts[CHAIN[3]] = ['http429']
        self.assertEqual(self.request(CHAIN[3])[0], 429)
        self.assertAlmostEqual(self.gate.cooling_left(CHAIN[3]), 30, delta=2)

    def test_http_504_moves_to_next_model_and_sets_it_aside(self):
        self.upstream.scripts[CODER] = ['http504']
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE, CODER_RESERVE])
        self.assertAlmostEqual(self.gate.cooling_left(CODER), 300, delta=2)

    def test_stalled_model_is_not_waited_on_again_by_the_next_request(self):
        self.gate.first_event_seconds = (.6, .6)
        self.upstream.scripts[CODER] = ['stall']
        self.assertEqual(self.request()[0], 200)
        start = time.monotonic()
        self.assertEqual(self.request()[0], 200)
        self.assertLess(time.monotonic() - start, .5)  # no second wait on the stalled model
        self.assertEqual(self.upstream.seen, [CODER, CODER_RESERVE, CODER_RESERVE])

    def test_chain_budget_stops_before_another_full_wait(self):
        self.gate.first_event_seconds = (.5, .5)
        self.gate.chain_seconds = 1.6
        for model in CHAIN:
            self.upstream.scripts[model] = ['stall']
        start = time.monotonic()
        status, headers, data = self.request()
        self.assertLess(time.monotonic() - start, 3)
        self.assertEqual(status, 504)
        self.assertEqual(headers['x-should-retry'], 'false')
        self.assertIn('prazo total da cadeia esgotado', json.loads(data)['error']['message'])
        self.assertLess(len(self.upstream.seen), len(CHAIN))

    def test_events_are_saved_as_they_happen(self):
        with tempfile.TemporaryDirectory() as folder:
            self.gate.events_path = Path(folder) / 'modelos-utilizados.json'
            self.upstream.scripts[CODER] = ['stream429']
            self.assertEqual(self.request()[0], 200)
            saved = json.loads(self.gate.events_path.read_text(encoding='utf-8'))
            self.assertEqual([(e['model'], e['outcome']) for e in saved], [(CODER, 'reserve-next'), (CODER_RESERVE, 'response')])


class ClassificationTests(unittest.TestCase):
    def test_stream_failure_classification(self):
        model = CODER
        cases = {
            RATE_LIMITED.split(b'data: ')[1].decode(): (429, None, True),
            '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}': (529, None, False),
            '{"error":{"message":"Upstream stream failed before completion.","type":"stream_error"}}': (503, None, False),
            '{"error":{"message":"Provider returned error","code":429}}': (429, None, True),
            '{"error":{"message":"Rate limit","type":"rate_limit_error","retry_after_seconds":42}}': (429, 42, True),
            '{"error":{"message":"Model not found","type":"invalid_request_error","code":"model_not_found"}}': (503, None, False),
        }
        for data, expected in cases.items():
            self.assertEqual(gateway.stream_failure(data, model), expected, data)
        for data in ('{"error":{"message":"Invalid API key provided","type":"authentication_error"}}',
                     '{"error":{"message":"Payment required","type":"billing_error"}}',
                     '{"error":{"message":"prompt is too long","type":"invalid_request_error"}}',
                     '{"error":{"message":"denied","type":"permission_error"}}'):
            self.assertIsNone(gateway.stream_failure(data, model), data)

    def test_first_event_wait_grows_with_request_size_and_is_capped(self):
        gate = gateway.Gateway('synthetic-local-key', {}, 'http://127.0.0.1:20128')
        try:
            self.assertEqual(gate.first_event_timeout(0), 60)
            self.assertAlmostEqual(gate.first_event_timeout(16384 * 30), 90)
            self.assertEqual(gate.first_event_timeout(64 * 1024 * 1024), 300)
        finally:
            gate.server_close()


if __name__ == '__main__':
    unittest.main()
