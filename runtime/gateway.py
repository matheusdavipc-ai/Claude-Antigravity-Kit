"""Ephemeral loopback filter. Calls only explicit OpenRouter free variants."""
import http.client
import json
import math
import re
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from context_config import response_budget
from core import KIT, ROLES, MODELS, get_catalog, safe_candidate, MODEL_NAMES, PRIMARY_ROLES, atomic_json

# Statuses that mean "this model is unavailable now", never "this request is wrong".
RESERVE_STATUSES = (404,408,429,500,502,503,504,529)
# An unavailable model is set aside for 5 min, or for its Retry-After within these bounds,
# so later requests go straight to the next model instead of waiting on it again.
COOLDOWN_SECONDS = (15, 300, 900)  # minimum, default, maximum
# OmniRoute answers a slow stream with HTTP 200 and keepalive pings while it cycles accounts.
# Wait at most this long for the first real event: base, plus 1 s per 16 KB of request, capped.
FIRST_EVENT_SECONDS = (60, 300)
FIRST_EVENT_BYTES_PER_SECOND = 16384
# Whole chain, all models together: stays below the native client's 600 s request timeout,
# so a long chain never makes the client resend the request.
CHAIN_SECONDS = 420
PRECOMMIT_LIMIT = 1024*1024

class Gateway(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, upstream_token, catalog=None, upstream='http://127.0.0.1:20128', testing=False, transport='omniroute', events_path=None):
        super().__init__(('127.0.0.1', 0), Handler)
        self.token = secrets.token_urlsafe(32)
        self.upstream_token = upstream_token
        self.upstream = urlsplit(upstream)
        self.transport = transport
        if transport not in ('omniroute', 'openrouter'):
            self.server_close()
            raise ValueError('Transporte desconhecido.')
        if not testing and (transport != 'omniroute' or self.upstream.scheme != 'http' or self.upstream.hostname not in ('127.0.0.1','localhost','::1') or self.upstream.path not in ('','/') or self.upstream.username or self.upstream.query or self.upstream.fragment):
            self.server_close()
            raise ValueError('O router exige OmniRoute local; upstream externo bloqueado.')
        self.catalog = catalog if catalog is not None else get_catalog()
        self.catalog_time = time.monotonic()
        self.context_ceiling = {model: item.get('context') for model, item in self.catalog.items()}
        self.active = 0
        self.lock = threading.Lock()
        self.events = []
        self.cooldown_seconds = COOLDOWN_SECONDS
        self.first_event_seconds = FIRST_EVENT_SECONDS
        self.chain_seconds = CHAIN_SECONDS
        self.cooling = {}
        # Saved after every event, so a closed terminal still leaves the record behind.
        self.events_path = events_path

    def cool(self, model, seconds=None):
        low, default, high = self.cooldown_seconds
        seconds = default if seconds is None else max(low, min(high, seconds))
        with self.lock:
            self.cooling[model] = max(self.cooling.get(model, 0), time.monotonic() + seconds)

    def cooling_left(self, model):
        with self.lock:
            return max(0.0, self.cooling.get(model, 0) - time.monotonic())

    def first_event_timeout(self, size):
        base, ceiling = self.first_event_seconds
        return min(ceiling, base + size / FIRST_EVENT_BYTES_PER_SECOND)

    def fresh_catalog(self):
        if time.monotonic() - self.catalog_time > 300:
            self.catalog = get_catalog()  # Fail closed if refresh fails.
            self.catalog_time = time.monotonic()
        return self.catalog

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    def log_message(self, *args):
        pass

    def authenticated(self):
        provided = self.headers.get('Authorization','').removeprefix('Bearer ')
        return secrets.compare_digest(provided, self.server.token)

    def send_json(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.authenticated():
            return self.send_json(401, {'error':{'type':'authentication_error','message':'Local gateway authentication required'}})
        if self.path.split('?')[0] in ('/v1/models','/api/v1/models'):
            return self.send_json(200, {'data':[{'id':model,'type':'model','display_name':name,'created_at':'2026-10-18T00:00:00Z'} for model,name in MODEL_NAMES.items()], 'has_more':False})
        return self.send_json(404, {'error':{'message':'Unsupported local endpoint'}})

    def do_POST(self):
        if not self.authenticated():
            # Drain a small body before closing so Windows does not reset the 401 response.
            try:
                length = int(self.headers.get('Content-Length','0'))
                if 0 < length <= 4096:
                    self.connection.settimeout(.5)
                    self.rfile.read(length)
            except (ValueError,OSError):
                pass
            finally:
                self.connection.settimeout(180)
            return self.send_json(401, {'error':{'type':'authentication_error','message':'Local gateway authentication required'}})
        path = self.path.split('?')[0]
        if path not in ('/v1/messages','/v1/messages/count_tokens'):
            return self.send_json(403, {'error':{'type':'permission_error','message':'Endpoint blocked by free-model filter'}})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 32*1024*1024:
                return self.send_json(413, {'error':{'message':'Invalid request size'}})
            body = json.loads(self.rfile.read(length))
            requested = body.get('model','').removesuffix('[1m]')
            role = PRIMARY_ROLES.get(requested, requested)
            if role in ROLES:
                candidates = ROLES[role]
            elif role in MODELS:
                # Explicit model requests do not acquire an unrelated role's reserve.
                candidates = (role,)
            else:
                return self.send_json(403, {'error':{'type':'permission_error','message':'Model outside the mandatory free team'}})
            visual = role == 'router-visual' or contains_image(body)
            catalog = self.server.fresh_catalog()
            candidates = [m for m in candidates if safe_candidate(m, catalog, visual)]
            if not candidates:
                return self.send_json(503, {'error':{'type':'api_error','message':'No verified free compatible model for this role'}})
            if any(isinstance(self.server.context_ceiling.get(model), int) and catalog[model].get('context', 0) < self.server.context_ceiling[model] for model in candidates):
                return self.send_json(409, {'error':{'type':'invalid_request_error','message':'Provider context limit decreased; restart clauderouter to recalculate safe compaction before continuing'}})
            if path == '/v1/messages':
                budget = response_budget(role, candidates, catalog)
                requested_output = body.get('max_tokens', budget)
                if not isinstance(requested_output, int) or isinstance(requested_output, bool) or requested_output <= 0:
                    return self.send_json(400, {'error':{'type':'invalid_request_error','message':'max_tokens must be a positive integer'}})
                body['max_tokens'] = min(requested_output, budget)
            # No advanced Anthropic-only reasoning/effort parameters on arbitrary models.
            body.pop('thinking',None)
            body.pop('output_config',None)
            body.pop('speed',None)
            body.pop('service_tier',None)
            # Remove upstream routing overrides supplied by caller.
            body.pop('models',None)
            body.pop('route',None)
            body.pop('provider',None)
            body.pop('plugins',None)
            body.pop('web_search_options',None)
            # Hosted search tools can incur separate charges; keep ordinary function tools.
            if 'tools' in body:
                body['tools'] = [tool for tool in body['tools'] if tool.get('type','custom') == 'custom']
            # A model that was just unavailable is skipped instead of cycling through it again.
            available = [m for m in candidates if not self.server.cooling_left(m)]
            if not available:
                wait = math.ceil(min(self.server.cooling_left(m) for m in candidates))
                self.record(role,candidates[0],'blocked-cooling',429)
                return self.send_unavailable(429, role, candidates, 'todos os modelos em espera apos falha recente', wait)
            with self.server.lock:
                self.server.active += 1
            chain_end = time.monotonic() + self.server.chain_seconds
            try:
                for index, model in enumerate(available):
                    last = index + 1 == len(available)
                    remaining = chain_end - time.monotonic()
                    if remaining <= 1:
                        # Budget spent on earlier models: report instead of starting another wait.
                        self.record(role,model,'blocked-chain-deadline',504)
                        return self.send_unavailable(504, role, available[:index], 'prazo total da cadeia esgotado', self.server.cooldown_seconds[1])
                    body['model'] = ('openrouter/' if self.server.transport == 'omniroute' else '') + model
                    payload = json.dumps(body).encode()
                    cls = http.client.HTTPSConnection if self.server.upstream.scheme == 'https' else http.client.HTTPConnection
                    connection = cls(self.server.upstream.hostname, self.server.upstream.port, timeout=max(5, min(180, remaining)))
                    headers = {'Content-Type':'application/json','Authorization':'Bearer '+self.server.upstream_token,
                               'anthropic-version':self.headers.get('anthropic-version','2023-06-01')}
                    # Preserve authentic harness attribution; never fabricate a different app.
                    for key in ('User-Agent','X-App','X-Title','HTTP-Referer','X-OpenRouter-Title','X-Stainless-Lang','X-Stainless-Package-Version'):
                        if self.headers.get(key):
                            headers[key] = self.headers[key]
                    try:
                        connection.request('POST',path if self.server.transport == 'omniroute' else '/api'+path,payload,headers)
                        upstream_socket = connection.sock
                        response = connection.getresponse()
                    except (OSError, http.client.HTTPException):
                        connection.close()
                        # Transport outcome uncertain: never replay to another model.
                        return self.send_json(502, {'error':{'type':'api_error','message':'Upstream transport failure; no automatic replay'}})
                    restricted_model = False
                    buffered = None
                    if response.status == 403:
                        buffered = response.read()
                        # A model-specific harness eligibility refusal is unavailability,
                        # not invalid credentials. Other 403s never trigger reserve.
                        restricted_model = b'only available on agentic harnesses' in buffered and model.encode() in buffered
                    if response.status in RESERVE_STATUSES or restricted_model:
                        self.server.cool(model, retry_after(response.getheader('Retry-After')))
                    if (response.status in RESERVE_STATUSES or restricted_model) and not last:
                        if buffered is None:
                            response.read()
                        connection.close()
                        self.record(role,model,'reserve-next',response.status)
                        print('[clauderouter] '+role+': '+MODEL_NAMES.get(model,model)+' indisponivel (HTTP '+str(response.status)+'); proximo: '+MODEL_NAMES.get(available[index+1],available[index+1]),flush=True)
                        continue
                    if (response.status == 200 and path == '/v1/messages'
                            and 'text/event-stream' in (response.getheader('Content-Type') or '').lower()):
                        # Nothing reaches the client until the first real event, so a failure
                        # reported inside the stream can still move to the reserve without
                        # replaying anything the client has seen.
                        deadline = min(chain_end, time.monotonic() + self.server.first_event_timeout(len(payload)))
                        outcome, buffered, failure = first_event(response, upstream_socket, model, deadline)
                        if outcome == 'reset':
                            connection.close()
                            return self.send_json(502, {'error':{'type':'api_error','message':'Upstream transport failure; no automatic replay'}})
                        if outcome in ('failure', 'timeout'):
                            connection.close()  # Ends the upstream attempt; OmniRoute stops its pings.
                            status, wait, _ = failure if outcome == 'failure' else (504, None, True)
                            # Rate limit, overload or silence: the model sits out its cooldown.
                            self.server.cool(model, wait)
                            self.record(role,model,'reserve-next' if not last else 'blocked',status)
                            if not last:
                                reason = 'sem primeiro evento no prazo' if outcome == 'timeout' else 'HTTP '+str(status)+' no stream'
                                print('[clauderouter] '+role+': '+MODEL_NAMES.get(model,model)+' indisponivel ('+reason+'); proximo: '+MODEL_NAMES.get(available[index+1],available[index+1]),flush=True)
                                continue
                            if outcome == 'timeout':
                                return self.send_unavailable(504, role, available, 'sem resposta dentro do prazo', self.server.cooldown_seconds[1])
                            if status == 429:
                                return self.send_unavailable(429, role, available, 'limite de requisicoes no provedor gratuito', math.ceil(self.server.cooling_left(model)) or None)
                            return self.send_unavailable(status, role, available, 'indisponivel no provedor', None)
                        upstream_socket.settimeout(180)
                    selected = response.getheader('X-OmniRoute-Selected-Connection-Id')
                    self.record(role,model,'response',response.status,selected)
                    self.send_response(response.status)
                    for key in ('Content-Type','Retry-After'):
                        if response.getheader(key):
                            self.send_header(key,response.getheader(key))
                    self.send_header('X-Claude-Perfis-Model',model)
                    self.send_header('Connection','close')
                    self.end_headers()
                    try:
                        if buffered:
                            self.wfile.write(buffered)
                            self.wfile.flush()
                        while data := response.read1(65536):
                            self.wfile.write(data)
                            self.wfile.flush()
                    finally:
                        connection.close()
                    return
            finally:
                with self.server.lock:
                    self.server.active -= 1
        except (ValueError, KeyError, OSError):
            # Never send exception details, prompt bodies or credentials to logs/client.
            if not self.wfile.closed:
                try:
                    self.send_json(503, {'error':{'type':'api_error','message':'Local verification failed; request blocked'}})
                except OSError:
                    pass

    def send_unavailable(self, status, role, models, reason, wait):
        # Tell the caller to stop: the agent reports the blocked route instead of retrying it.
        names = ', '.join(MODEL_NAMES.get(m, m) for m in models) or 'nenhum modelo tentado'
        message = 'Rota '+role+' indisponivel ('+reason+'): '+names+'. Nenhum outro modelo sera tentado; informe o usuario.'
        if wait:
            message += ' Nova tentativa possivel em '+str(wait)+' s.'
        data = json.dumps({'type':'error','error':{'type':'rate_limit_error' if status == 429 else 'api_error','message':message}}).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('x-should-retry','false')
        if wait:
            self.send_header('Retry-After',str(wait))
        self.end_headers()
        self.wfile.write(data)

    def record(self, role, model, outcome, status, connection_id=None):
        event = {'time':time.time(),'role':role,'model':model,'outcome':outcome,'status':status}
        if connection_id:
            event['connection_id'] = connection_id
        with self.server.lock:
            self.server.events.append(event)
            if self.server.events_path:
                try:
                    atomic_json(self.server.events_path, self.server.events)
                except OSError:
                    pass  # The record is best effort; never fail a request over it.

def retry_after(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None

def first_event(response, upstream_socket, model, deadline):
    """Read SSE until the first event that is not a keepalive.

    Returns ('commit', bytes, None) to stream on, ('failure', bytes, (status, wait, rate_limited))
    for an unavailability error, ('timeout', None, None) or ('reset', None, None).
    """
    buffered = bytearray()
    block = []
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 'timeout', None, None
        try:
            upstream_socket.settimeout(min(remaining, 180))
            line = response.readline(65536)
        except socket.timeout:
            return 'timeout', None, None
        except (OSError, http.client.HTTPException):
            return 'reset', None, None
        if not line:
            return 'commit', bytes(buffered), None
        buffered += line
        text = line.decode('utf-8', 'replace').rstrip('\r\n')
        if text:
            block.append(text)
            if len(buffered) > PRECOMMIT_LIMIT:
                return 'commit', bytes(buffered), None
            continue
        if not block:
            continue
        event = next((l[6:].strip() for l in block if l.startswith('event:')), '')
        data = '\n'.join(l[5:].strip() for l in block if l.startswith('data:'))
        block = []
        if event == 'ping' or not (event or data):
            continue  # OmniRoute keepalive or SSE comment.
        if event == 'error' or is_error_data(data):
            failure = stream_failure(data, model)
            return ('failure', bytes(buffered), failure) if failure else ('commit', bytes(buffered), None)
        return 'commit', bytes(buffered), None

def is_error_data(data):
    try:
        value = json.loads(data)
    except ValueError:
        return False
    return isinstance(value, dict) and (value.get('type') == 'error' or 'error' in value)

def stream_failure(data, model):
    """Classify an error sent inside a 200 stream. None means: not unavailability, no reserve."""
    try:
        value = json.loads(data)
    except ValueError:
        value = data
    error = value.get('error', value) if isinstance(value, dict) else value
    kind = code = ''
    status = wait = None
    if isinstance(error, dict):
        kind = str(error.get('type', '')).lower()
        code = str(error.get('code', '')).lower()
        status = next((v for v in (error.get('status_code'), error.get('status'), error.get('code')) if isinstance(v, int) and not isinstance(v, bool)), None)
        wait = retry_after(error.get('retry_after_seconds', value.get('retry_after_seconds') if isinstance(value, dict) else None))
    text = (json.dumps(error, ensure_ascii=False) if not isinstance(error, str) else error).lower()
    if 'only available on agentic harnesses' in text and model.lower() in text:
        return 403, None, False
    if kind in ('authentication_error', 'permission_error', 'billing_error') or status in (400, 401, 402, 403, 413):
        return None
    if 'rate_limit' in kind or 'rate_limit' in code or status == 429 or re.search(r'rate.?limit|too many requests|\b429\b|quota', text):
        return 429, wait, True
    if kind == 'overloaded_error' or status == 529 or 'overloaded' in text:
        return 529, wait, False
    if kind == 'invalid_request_error' and status != 404 and 'not_found' not in code:
        return None
    if status in RESERVE_STATUSES:
        return status, wait, False
    if kind in ('server_error', 'api_error', 'stream_error', 'timeout_error', 'not_found_error') or 'not_found' in code:
        return 503, wait, False
    return None

def contains_image(value):
    if isinstance(value,dict):
        return value.get('type') in ('image','image_url') or any(contains_image(v) for v in value.values())
    if isinstance(value,list):
        return any(contains_image(v) for v in value)
    return False
