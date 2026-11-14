"""Save tactics that worked, and propose playbook edits from threads that did not."""

from __future__ import annotations

import difflib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore

from src.agent.llm import build_llm, deterministic_failure_analysis, deterministic_win
from src.config import get_settings
from src.tools.crm import load_failure_threads, save_reflection_log
from src.tools.knowledge_base import PLAYBOOK_PATH

logger = logging.getLogger(__name__)


def tactic_namespace(profile: dict[str, Any]) -> tuple[str, str]:
    """Store namespace ``("tactics", industry_or_persona)``."""

    raw = str(profile.get("industry") or profile.get("role") or "general")
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-") or "general"
    return ("tactics", slug[:64])


def extract_winning_tactic(state: dict[str, Any], store: BaseStore, llm: Any | None = None) -> dict[str, Any]:
    """Summarize a booked thread or a recovered objection and save it for similar leads."""

    heuristic = None
    if llm is not None:
        try:
            heuristic = llm.summarize_win(state)
        except Exception:
            logger.exception("win summary failed")
            heuristic = None
    if not isinstance(heuristic, dict) or not heuristic.get("text"):
        heuristic = deterministic_win(state)
    profile = state.get("lead_profile") or {}
    namespace = tactic_namespace(profile)
    stamp = int(datetime.now(timezone.utc).timestamp())
    angle = re.sub(r"[^a-z0-9]+", "-", str(heuristic.get("angle") or "angle").lower()).strip("-") or "angle"
    key = f"{state.get('lead_id')}-{angle}-{stamp}"
    value = {
        "text": str(heuristic.get("text") or ""),
        "heuristic": str(heuristic.get("heuristic") or heuristic.get("text") or ""),
        "angle": heuristic.get("angle") or state.get("last_angle_used") or "",
        "persona": heuristic.get("persona") or profile.get("role") or "",
        "industry": heuristic.get("industry") or profile.get("industry") or "",
        "outcome": heuristic.get("outcome") or state.get("outcome_label") or state.get("stage"),
        "lead_id": state.get("lead_id"),
    }
    store.put(namespace, key, value)
    logger.info("stored tactic namespace=%s key=%s", namespace, key)
    return value


def run_nightly_reflection(
    *,
    output_dir: Path | str | None = None,
    llm: Any | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Scan ghosting and unsubscribe threads and write a playbook diff plus a JSON report."""

    moment = now or datetime.now(timezone.utc)
    directory = Path(output_dir) if output_dir is not None else get_settings().reflection_dir()
    directory.mkdir(parents=True, exist_ok=True)
    records = load_failure_threads()
    analyzer = llm if llm is not None else build_llm()
    try:
        analysis = analyzer.analyze_failures(records)
    except Exception:
        logger.exception("failure analysis failed; using deterministic clusters")
        analysis = deterministic_failure_analysis(records)
    if not isinstance(analysis, dict):
        analysis = deterministic_failure_analysis(records)
    clusters = list(analysis.get("clusters") or [])
    improvements = list(analysis.get("prompt_improvements") or [])
    original = PLAYBOOK_PATH.read_text(encoding="utf-8")
    if improvements or clusters:
        lines = ["", f"## Proposed additions ({moment.strftime('%Y-%m-%d')})", ""]
        for cluster in clusters:
            lines.append(
                f"- {cluster.get('pattern')} (n={cluster.get('count')}): {cluster.get('proposal')}"
            )
        for item in improvements:
            target = item.get("target") if isinstance(item, dict) else "prompt"
            change = item.get("change") if isinstance(item, dict) else str(item)
            lines.append(f"- prompt `{target}`: {change}")
        candidate = original.rstrip() + "\n" + "\n".join(lines) + "\n"
    else:
        candidate = original
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="data/playbook.md",
            tofile="playbook_candidate.md",
        )
    )
    report = {
        "generated_at": moment.astimezone(timezone.utc).isoformat(),
        "threads_scanned": len(records),
        "clusters": clusters,
        "prompt_improvements": improvements,
        "source": analysis.get("source") or "deterministic",
        "playbook_diff": diff,
        "output_dir": str(directory),
    }
    (directory / "playbook_candidate.md").write_text(candidate, encoding="utf-8")
    (directory / "playbook_candidate.diff").write_text(diff, encoding="utf-8")
    (directory / "reflection_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = f"scanned {len(records)} failed threads; {len(clusters)} clusters"
    try:
        report["reflection_log_id"] = save_reflection_log(summary, json.dumps(report), diff)
    except Exception:
        logger.exception("failed to persist reflection log")
    return report
