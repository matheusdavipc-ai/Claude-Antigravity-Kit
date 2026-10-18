"""Published model windows and reserve-aware compaction; no fake Claude identities."""
import json
from pathlib import Path

SNAPSHOT = json.loads((Path(__file__).resolve().parents[1] / 'models.json').read_text(encoding='utf-8'))


def context_plan(catalog=None):
    catalog = catalog or {}
    limits = {}
    for model, snapshot in SNAPSHOT['limits'].items():
        current = catalog.get(model)
        item = snapshot if current is None else current
        window, output = item.get('context'), item.get('max_output')
        if not isinstance(window, int) or window <= 0 or not isinstance(output, int) or output <= 0:
            raise ValueError('Verified context/output metadata required: ' + model)
        limits[model] = {'context': window, 'max_output': output}
    small = [item['context'] for item in limits.values() if item['context'] < 1000000]
    baseline = min(small) if small else 256000
    result = {}
    primary = {pair[0]: role for role, pair in SNAPSHOT['roles'].items()}
    for model, item in limits.items():
        pair = SNAPSHOT['roles'][primary[model]] if model in primary else [model]
        window = min(limits[candidate]['context'] for candidate in pair)
        output = min(65536, *(limits[candidate]['max_output'] for candidate in pair))
        # [1m] is an official Claude Code hint, stripped before calling OpenRouter.
        native = 1000000 if item['context'] >= 1000000 else baseline
        compact = min(window, native) - output - 16384
        if compact < 100000:
            raise ValueError('Context too small for safe native auto-compaction: ' + model)
        result[model] = {'published_context': item['context'], 'published_max_output': item['max_output'],
                         'route_context': window, 'native_context': native, 'output_budget': output,
                         'compact_at': compact}
    return result


def native_model(model, plan=None):
    plan = plan or context_plan()
    base = model.removesuffix('[1m]')
    if base not in plan:
        return model
    return base + ('[1m]' if plan[base]['published_context'] >= 1000000 else '')


def context_env(plan=None):
    plan = plan or context_plan()
    small = [item['native_context'] for item in plan.values() if item['published_context'] < 1000000]
    return {'CLAUDE_CODE_MAX_CONTEXT_TOKENS': str(min(small) if small else 256000),
            'CLAUDE_CODE_DISABLE_1M_CONTEXT': '',
            'DISABLE_COMPACT': '', 'CLAUDE_CODE_AUTO_COMPACT_WINDOW': '',
            'CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT': ''}


def context_settings(plan=None):
    plan = plan or context_plan()
    settings = {}
    for model, item in plan.items():
        for key in {model, native_model(model, plan)}:
            settings[key] = {'autoCompactWindow': item['compact_at']}
    return settings


def context_picker(picker, plan=None):
    plan = plan or context_plan()
    return {**picker, 'options': [{**row, 'model': native_model(row['model'], plan)} for row in picker['options']]}


def response_budget(role, candidates, catalog):
    limits = []
    for model in candidates:
        item = catalog.get(model, {})
        value = item.get('max_output')
        if not isinstance(value, int) or value <= 0 or not isinstance(item.get('context'), int) or item['context'] <= 0:
            raise ValueError('Verified model metadata required before inference')
        limits.append(value)
    return min(65536, *limits)
