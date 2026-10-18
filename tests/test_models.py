import http.client
import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import test_profiles
import core

class ModelNamesTests(test_profiles.RoutingTests):
    def test_original_ids_keep_role_reserves(self):
        for role, pair in core.ROLES.items():
            self.upstream.statuses = [503, 200]
            self.assertEqual(self.request(pair[0])[0], 200)
            self.assertEqual([row['model'] for row in self.upstream.seen[-2:]], list(pair))

    def test_discovery_contains_seven_original_names(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.gate.server_port, timeout=5)
        connection.request('GET', '/v1/models', headers={'Authorization': 'Bearer ' + self.gate.token})
        response = connection.getresponse()
        data = json.loads(response.read())
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertEqual({row['id']: row['display_name'] for row in data['data']}, core.MODEL_NAMES)
        self.assertEqual(len(data['data']), 7)

    def test_direct_reserve_has_no_unrelated_fallback(self):
        self.upstream.statuses = [503, 200]
        self.assertEqual(self.request(core.ROLES['router-orchestrator'][1])[0], 503)
        self.assertEqual(len(self.upstream.seen), 1)

    def test_output_budget_is_compatible_with_reserve(self):
        pair = core.ROLES['router-coder']
        self.gate.catalog[pair[0]]['max_output'] = 65536
        self.gate.catalog[pair[1]]['max_output'] = 32768
        self.upstream.statuses = [503, 200]
        self.assertEqual(self.request(pair[0] + '[1m]', max_tokens=200000)[0], 200)
        self.assertEqual([row['max_tokens'] for row in self.upstream.seen], [32768, 32768])
        self.assertEqual([row['model'] for row in self.upstream.seen], list(pair))

    def test_invalid_response_budget_never_reaches_provider(self):
        self.assertEqual(self.request(max_tokens='invalid')[0], 400)
        self.assertEqual(self.upstream.seen, [])

    def test_context_shrink_blocks_provider_until_restart(self):
        model = core.ROLES['router-coder'][1]
        self.gate.catalog[model]['context'] = 180000
        self.assertEqual(self.request()[0], 409)
        self.assertEqual(self.upstream.seen, [])
