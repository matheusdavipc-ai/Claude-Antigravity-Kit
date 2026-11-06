"""Existing OmniRoute key: model permissions follow the kit list, same key, no secret output."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
import core

BRIDGE = ROOT / 'runtime/omniroute_bridge.mjs'
KIT_MODELS = ['openrouter/' + m for m in sorted(core.MODELS)]
KEY_ID = 'key-fixture-1'
MASKED = 'sk-fixtu****wxyz'

# Protocol double of the OmniRoute API client shipped in the package (bin/cli/api.mjs).
FIXTURE = r"""
import fs from 'node:fs';
const p = process.env.FIXTURE_STATE;
export async function apiFetch(path, o) {
  const s = JSON.parse(fs.readFileSync(p));
  if (s.down) throw new Error('ECONNREFUSED');
  const name = o.method + ' ' + path.split('?')[0];
  if (s.fail && s.fail[name]) return { ok: false, status: s.fail[name], json: async () => ({}) };
  let data = {};
  if (o.method === 'GET') {
    if (path.startsWith('/api/providers?')) data = { connections: s.connections };
    else if (path === '/api/settings') data = s.settings;
    else if (path.startsWith('/api/keys/')) {
      const k = s.keys[decodeURIComponent(path.split('/').pop())];
      if (!k) return { ok: false, status: 404, json: async () => ({}) };
      data = { ...k, key: k.masked };
    }
  } else {
    s.writes.push(name);
    if (path === '/api/settings') Object.assign(s.settings, o.body);
    else if (path.startsWith('/api/keys/')) Object.assign(s.keys[decodeURIComponent(path.split('/').pop())], o.body);
    else Object.assign(s.connections.find(c => c.id === path.split('/').pop()), o.body);
    fs.writeFileSync(p, JSON.stringify(s));
  }
  return { ok: true, json: async () => data };
}
"""


@unittest.skipUnless(shutil.which('node'), 'Node required')
class ExistingKeyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        package = self.root / 'package/bin/cli'
        package.mkdir(parents=True)
        (package / 'api.mjs').write_text(FIXTURE, encoding='utf-8')
        self.state_file = self.root / 'state.json'
        self.backup = self.root / 'pool-before.json'

    def tearDown(self):
        self.tmp.cleanup()

    def state(self, allowed, strategy='fill-first', priorities=(1, 2), **extra):
        value = {
            'connections': [{'id': 'c' + str(i), 'provider': 'openrouter', 'name': 'main' + str(i), 'isActive': True, 'priority': p}
                            for i, p in zip((1, 2), priorities)],
            'settings': {'providerStrategies': {'openrouter': {'fallbackStrategy': strategy}}},
            'keys': {KEY_ID: {'id': KEY_ID, 'name': 'Claude Antigravity Kit 1', 'modelAccessMode': 'restricted',
                              'allowedModels': allowed, 'allowedCombos': [], 'masked': MASKED}},
            'writes': [],
        }
        value.update(extra)
        core.atomic_json(self.state_file, value)

    def run_bridge(self, **request):
        payload = {'url': 'http://127.0.0.1:20128', 'package': str(self.root / 'package'), 'backup': str(self.backup),
                   'createKey': False, 'keyId': KEY_ID, 'models': KIT_MODELS, **request}
        result = subprocess.run(['node', str(BRIDGE)], input=json.dumps(payload), text=True, capture_output=True,
                                env={**os.environ, 'FIXTURE_STATE': str(self.state_file)}, timeout=60)
        return result, core.read_json(self.state_file)

    def test_old_list_is_replaced_on_the_same_key_and_second_run_changes_nothing(self):
        old = ['openrouter/thinkingmachines/inkling:free', 'openrouter/retired/model:free']
        self.state(old)
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 0, result.stderr)
        key = data['keys'][KEY_ID]
        self.assertEqual(sorted(key['allowedModels']), KIT_MODELS)
        self.assertEqual(key['modelAccessMode'], 'restricted')
        self.assertEqual(list(data['keys']), [KEY_ID])  # no new key
        self.assertEqual(data['writes'], ['PATCH /api/keys/' + KEY_ID])
        out = json.loads(result.stdout)
        self.assertTrue(out['key_updated'])
        self.assertEqual(out['key_id'], KEY_ID)
        self.assertIsNone(out.get('secret'))
        # The backup holds the previous permissions and never the (masked) secret.
        backup = core.read_json(self.backup)
        self.assertEqual(backup['key']['allowedModels'], old)
        self.assertNotIn(MASKED, self.backup.read_text(encoding='utf-8'))
        self.assertNotIn(MASKED, result.stdout + result.stderr)
        # Idempotent: the second run performs no write at all.
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(data['writes'], ['PATCH /api/keys/' + KEY_ID])
        self.assertFalse(json.loads(result.stdout)['key_updated'])

    def test_list_already_correct_writes_nothing(self):
        self.state(list(reversed(KIT_MODELS)))  # order does not matter
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(data['writes'], [])
        self.assertFalse(json.loads(result.stdout)['key_updated'])

    def test_refused_key_update_changes_nothing(self):
        # Strategy and priorities would also need changes; none may happen once the key update is refused.
        self.state(['openrouter/retired/model:free'], strategy='round-robin', priorities=(5, 5),
                   fail={'PATCH /api/keys/' + KEY_ID: 403})
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['writes'], [])
        self.assertEqual(data['keys'][KEY_ID]['allowedModels'], ['openrouter/retired/model:free'])
        self.assertEqual(data['settings']['providerStrategies']['openrouter']['fallbackStrategy'], 'round-robin')
        self.assertEqual(result.stdout, '')
        self.assertNotIn(MASKED, result.stderr)

    def test_stopped_server_changes_nothing(self):
        self.state(['openrouter/retired/model:free'], down=True)
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['writes'], [])
        self.assertFalse(self.backup.exists())

    def test_refused_key_read_changes_nothing(self):
        self.state(['openrouter/retired/model:free'], fail={'GET /api/keys/' + KEY_ID: 401})
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['writes'], [])

    def test_later_failure_restores_previous_key_permissions(self):
        old = ['openrouter/retired/model:free']
        self.state(old, strategy='round-robin', fail={'PATCH /api/settings': 500})
        result, data = self.run_bridge()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['keys'][KEY_ID]['allowedModels'], old)
        self.assertEqual(data['writes'], ['PATCH /api/keys/' + KEY_ID, 'PATCH /api/keys/' + KEY_ID])

    def test_missing_key_id_or_models_fails_before_any_call(self):
        self.state(['openrouter/retired/model:free'])
        for request in ({'keyId': ''}, {'models': []}):
            result, data = self.run_bridge(**request)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(data['writes'], [])
            self.assertFalse(self.backup.exists())


if __name__ == '__main__':
    unittest.main()
