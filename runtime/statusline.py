"""Status line nativa e leve para o Claude Code (modelo, contexto, custo e cota 5h/7d)."""

from __future__ import annotations

import datetime as _dt
import json
import sys
import time
from typing import Any


def _fmt_k(tokens: int | float) -> str:
    val = float(tokens)
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.0f}k"
    return f"{int(val)}"


def _fmt_reset(resets_at: Any) -> str:
    if resets_at is None:
        return ""
    now = time.time()
    ts: float | None = None
    if isinstance(resets_at, (int, float)):
        ts = float(resets_at)
        if ts > 1e12:
            ts /= 1000.0
    elif isinstance(resets_at, str) and resets_at.strip():
        raw = resets_at.strip()
        try:
            ts = float(raw)
        except ValueError:
            try:
                dt = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                ts = dt.timestamp()
            except ValueError:
                ts = None
    if ts is None:
        return ""
    rem = int(ts - now)
    if rem <= 0:
        return ""
    mins = rem // 60
    hours = mins // 60
    days = hours // 24
    if days > 0:
        return f" ({days}d{hours % 24}h)"
    if hours > 0:
        return f" ({hours}h{mins % 60:02d}m)"
    return f" ({mins}m)"


def _fmt_window(window: Any, label: str) -> str:
    if not isinstance(window, dict):
        return f"{label} --%"
    pct = window.get("used_percentage")
    if pct is None:
        return f"{label} --%"
    try:
        pct_num = float(pct)
    except (TypeError, ValueError):
        return f"{label} --%"
    reset_str = _fmt_reset(window.get("resets_at"))
    return f"{label} {pct_num:.0f}%{reset_str}"


def build_statusline(payload: dict[str, Any]) -> str:
    model_obj = payload.get("model")
    if isinstance(model_obj, dict):
        model_name = (
            model_obj.get("display_name")
            or model_obj.get("id")
            or model_obj.get("name")
            or "Claude"
        )
    elif isinstance(model_obj, str) and model_obj.strip():
        model_name = model_obj.strip()
    else:
        model_name = "Claude"

    ctx = payload.get("context_window")
    if not isinstance(ctx, dict):
        ctx = {}
    max_tok = int(ctx.get("context_window_size") or 200_000)
    usage = ctx.get("current_usage")
    used_tok = 0
    if isinstance(usage, dict):
        used_tok = int(
            (usage.get("input_tokens") or 0)
            + (usage.get("cache_creation_input_tokens") or 0)
            + (usage.get("cache_read_input_tokens") or 0)
        )
    if used_tok <= 0:
        used_tok = int(ctx.get("total_input_tokens") or 0)

    pct_raw = ctx.get("used_percentage")
    if pct_raw is not None:
        try:
            ctx_pct = float(pct_raw)
        except (TypeError, ValueError):
            ctx_pct = (used_tok / max_tok * 100.0) if max_tok > 0 else 0.0
    else:
        ctx_pct = (used_tok / max_tok * 100.0) if max_tok > 0 else 0.0
        if used_tok <= 0 and ctx_pct > 0:
            used_tok = int(max_tok * (ctx_pct / 100.0))

    if used_tok > 0:
        ctx_part = f"ctx {ctx_pct:.0f}% ({_fmt_k(used_tok)}/{_fmt_k(max_tok)})"
    else:
        ctx_part = f"ctx {ctx_pct:.0f}% (0/{_fmt_k(max_tok)})"

    cost_obj = payload.get("cost")
    cost_usd = 0.0
    if isinstance(cost_obj, dict):
        try:
            cost_usd = float(cost_obj.get("total_cost_usd") or 0.0)
        except (TypeError, ValueError):
            cost_usd = 0.0
    if 0 < cost_usd < 0.01:
        cost_part = f"${cost_usd:.3f}"
    else:
        cost_part = f"${cost_usd:.2f}"

    limits = payload.get("rate_limits")
    if not isinstance(limits, dict):
        limits = {}
    five_h = _fmt_window(limits.get("five_hour"), "5h")
    seven_d = _fmt_window(limits.get("seven_day"), "7d")

    return f"{model_name} | {ctx_part} | {cost_part} | {five_h} · {seven_d}"


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw and raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    sys.stdout.write(build_statusline(data) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

