import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import core
from context_config import context_plan, context_settings, native_model, SNAPSHOT


class ContextLimitsTests(unittest.TestCase):
    def test_every_route_leaves_space_for_response_and_reserve(self):
        plan = context_plan()
        self.assertEqual({key: list(value) for key, value in core.ROLES.items()}, SNAPSHOT['roles'])
        for role, pair in core.ROLES.items():
            limit = plan[pair[0]]
            for model in pair:
                self.assertLessEqual(limit['compact_at'] + limit['output_budget'] + 16384,
                                     SNAPSHOT['limits'][model]['context'])
                self.assertLessEqual(limit['output_budget'], SNAPSHOT['limits'][model]['max_output'])
        self.assertGreater(plan[core.ROLES['router-orchestrator'][0]]['compact_at'], 900000)
        self.assertLess(plan[core.ROLES['router-coder'][0]]['compact_at'], 262144)

    def test_only_verified_million_token_models_get_hint(self):
        for model, limit in context_plan().items():
            selected = native_model(model + '[1m]')
            self.assertEqual(selected.endswith('[1m]'), limit['published_context'] >= 1000000)
            self.assertEqual(context_settings()[selected]['autoCompactWindow'], limit['compact_at'])

    def test_provider_limit_change_reduces_compaction(self):
        model = core.ROLES['router-orchestrator'][1]
        catalog = {model: {'context': 300000, 'max_output': 65536}}
        plan = context_plan(catalog)
        main = plan[core.ROLES['router-orchestrator'][0]]
        self.assertLessEqual(main['compact_at'] + main['output_budget'] + 16384, 300000)

    def test_incomplete_metadata_fails_closed(self):
        with self.assertRaises(ValueError):
            context_plan({core.ROLES['router-orchestrator'][0]: {'context': 1000000}})
