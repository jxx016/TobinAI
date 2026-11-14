"""Chat-model adapter.

A real ``ChatModel`` is used when ``OPENAI_API_KEY`` or ``ANTHROPIC_API_KEY`` is set.
Otherwise ``MockChaseLLM`` returns the same structured shapes without a network call.
Opt-out, injection, and high-stakes gates are decided in code so a model cannot waive them.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agent.prompts import CLASSIFY_SYSTEM, DRAFT_SYSTEM, REFLECT_SYSTEM, WIN_SYSTEM
from src.agent.state import ANGLES, Stage
from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

SCHEDULED_FOLLOW_UP = "scheduled_follow_up"

Sentiment = Literal["neutral", "positive", "angry", "unsubscribe", "objection", "ready"]

_INJECTION_RE = re.compile(
    r"(ignore (all|any|previous|prior) instructions|"
    r"you are now|"
    r"system prompt|"
    r"developer message|"
    r"<\s*/?\s*system\s*>|"
    r"\btool_call\b|"
    r"call send_email|"
    r"jailbreak|"
    r"reveal your (prompt|instructions))",
    re.IGNORECASE,
)
_OPT_OUT_RE = re.compile(
    r"(\bunsubscribe\b|\bopt[\s-]?out\b|\bremove me\b|"
    r"\bdo not (contact|email|text)\b|\bdon't (contact|email|text)\b|"
    r"\bstop (emailing|texting|messaging|contacting)\b|\bleave me alone\b)",
    re.IGNORECASE,
)
_EXACT_OPT_OUT = frozenset({"stop", "stop all", "unsubscribe", "cancel", "end", "quit"})
_DISQUAL_RE = re.compile(
    r"(\bnot interested\b|\bno thanks\b|\bno thank you\b|\bwrong person\b|"
    r"\bwe don't need\b|\bwe do not need\b|\bgo away\b)",
    re.IGNORECASE,
)
_BOOK_RE = re.compile(
    r"(\blet's book\b|\blets book\b|\bbook a\b|\bschedule a\b|\bgrab time\b|"
    r"\bready to (book|meet|talk)\b|\bset up a (call|time|meeting)\b|\b15[- ]minute\b)",
    re.IGNORECASE,
)
_ANGRY_RE = re.compile(
    r"(\bfurious\b|\bangry\b|\bunacceptable\b|\bridiculous\b|\boutraged\b|"
    r"\bpissed\b|\bthis is absurd\b|\bterrible service\b)",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(
    r"(\btoo expensive\b|\bpricing\b|\bprice\b|\bcosts? too much\b|\bout of (our )?budget\b)",
    re.IGNORECASE,
)
_DISCOUNT_ASK_RE = re.compile(
    r"(\bdiscount\b|\bcheaper\b|\bbetter (on )?price\b|\bdo better\b|"
    r"\bcustom pric\w*\b|\b% ?off\b|\bpercent off\b|\bknock off\b|\bcut the price\b)",
    re.IGNORECASE,
)
_VIP_RE = re.compile(r"(\benterprise\b|\bvip\b|\bprocurement\b|\bfortune\s?500\b)", re.IGNORECASE)


class IntentClassification(BaseModel):
    stage: Stage = "ENGAGED"
    requires_human_approval: bool = False
    approval_reason: str | None = None
    sentiment: Sentiment = "neutral"
    injection_detected: bool = False
    rationale: str = ""


class DraftOutput(BaseModel):
    message: str = Field(min_length=1)


class FailureClusterModel(BaseModel):
    pattern: str
    count: int = 0
    proposal: str
    lead_ids: list[str] = Field(default_factory=list)


class ReflectionAnalysis(BaseModel):
    clusters: list[FailureClusterModel] = Field(default_factory=list)
    prompt_improvements: list[dict[str, str]] = Field(default_factory=list)
    source: str = "model"


class WinHeuristic(BaseModel):
    text: str
    angle: str = ""
    persona: str = ""
    industry: str = ""
    outcome: str = ""


@dataclass
class DraftRequest:
    lead_profile: dict[str, Any]
    stage: str
    angle: str
    mode: Literal["outreach", "objection", "booking"]
    critic_feedback: str | None = None
    battlecard: str = ""
    booking_link: str | None = None
    history_snippet: str = ""
    winning_tactics: list[str] = field(default_factory=list)


class ChaseLLM(Protocol):
    def classify(self, state: dict[str, Any]) -> IntentClassification: ...

    def draft(self, request: DraftRequest) -> str: ...

    def analyze_failures(self, records: list[dict[str, Any]]) -> dict[str, Any]: ...

    def summarize_win(self, state: dict[str, Any]) -> dict[str, Any]: ...


def latest_message(state: dict[str, Any]) -> Any | None:
    messages = state.get("messages") or []
    return messages[-1] if messages else None


def is_scheduled_followup(state: dict[str, Any]) -> bool:
    message = latest_message(state)
    content = getattr(message, "content", "")
    return message.__class__.__name__ == "SystemMessage" and str(content).strip() == SCHEDULED_FOLLOW_UP


def latest_human_text(state: dict[str, Any]) -> str:
    for message in reversed(state.get("messages") or []):
        if message.__class__.__name__ == "HumanMessage":
            content = getattr(message, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def is_opt_out(text: str) -> bool:
    stripped = (text or "").strip().lower()
    if stripped in _EXACT_OPT_OUT:
        return True
    return bool(_OPT_OUT_RE.search(text or ""))


def injection_detected(text: str) -> bool:
    return bool(_INJECTION_RE.search(text or ""))


def strip_injection(text: str) -> str:
    """Drop sentences that try to override the agent. Opt-out is handled first."""

    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    kept = [part for part in parts if part.strip() and not _INJECTION_RE.search(part)]
    return " ".join(kept).strip()


def classify_by_rules(state: dict[str, Any]) -> IntentClassification:
    """Keyword policy used by the mock model and as a hard overlay on a live model."""

    stage = str(state.get("stage") or "NEW")
    if stage == "UNSUBSCRIBED":
        return IntentClassification(
            stage="UNSUBSCRIBED",
            sentiment="unsubscribe",
            rationale="prior opt-out stays in force",
        )
    if is_scheduled_followup(state) and stage in {"DISQUALIFIED", "BOOKED"}:
        return IntentClassification(stage=stage, rationale="terminal lead; follow-up will not send")  # type: ignore[arg-type]
    if is_scheduled_followup(state):
        return IntentClassification(stage="GHOSTING", rationale="scheduled chase with no new reply")

    text = latest_human_text(state)
    if not text:
        kept: Stage = stage if stage in {"NEW", "ENRICHED", "ENGAGED", "GHOSTING"} else "ENRICHED"  # type: ignore[assignment]
        return IntentClassification(stage=kept, rationale="no inbound message yet")

    if is_opt_out(text):
        return IntentClassification(
            stage="UNSUBSCRIBED",
            sentiment="unsubscribe",
            injection_detected=injection_detected(text),
            rationale="opt-out halts outreach immediately",
        )

    if injection_detected(text):
        # The whole payload is untrusted. Do not mine it for pricing, anger,
        # booking, or tool requests — those are the instructions we ignore.
        # Opt-out was already honored above.
        return IntentClassification(
            stage="ENGAGED",
            requires_human_approval=False,
            approval_reason=None,
            injection_detected=True,
            sentiment="neutral",
            rationale="prompt injection ignored; chase policy unchanged",
        )

    return _classify_clean_text(text)


def _classify_clean_text(text: str) -> IntentClassification:
    approval = False
    reason: str | None = None
    sentiment: Sentiment = "neutral"

    if _BOOK_RE.search(text):
        stage: Stage = "READY_TO_BOOK"
        sentiment = "ready"
    elif _DISQUAL_RE.search(text) and not _PRICE_RE.search(text):
        stage = "DISQUALIFIED"
        sentiment = "neutral"
    elif _ANGRY_RE.search(text) or _PRICE_RE.search(text) or _DISCOUNT_ASK_RE.search(text):
        stage = "OBJECTION"
        sentiment = "angry" if _ANGRY_RE.search(text) else "objection"
    else:
        stage = "ENGAGED"
        sentiment = "positive" if _BOOK_RE.search(text) else "neutral"

    if _ANGRY_RE.search(text):
        approval = True
        reason = "angry_sentiment"
    if _DISCOUNT_ASK_RE.search(text):
        approval = True
        reason = "custom_pricing"
        stage = "OBJECTION"
        sentiment = "objection"
    if _VIP_RE.search(text):
        approval = True
        if reason is None:
            reason = "enterprise_vip"

    return IntentClassification(
        stage=stage,
        requires_human_approval=approval,
        approval_reason=reason,
        sentiment=sentiment,
        rationale="rule classifier",
    )


def merge_safe(rules: IntentClassification, proposed: IntentClassification) -> IntentClassification:
    """Let a live model add nuance, never a looser safety decision."""

    if rules.injection_detected or rules.stage == "UNSUBSCRIBED":
        return rules
    if rules.stage in {"READY_TO_BOOK", "OBJECTION", "DISQUALIFIED", "BOOKED", "GHOSTING"}:
        return rules.model_copy(update={"rationale": proposed.rationale or rules.rationale})
    stage = proposed.stage if proposed.stage in {
        "ENGAGED",
        "OBJECTION",
        "READY_TO_BOOK",
        "GHOSTING",
        "DISQUALIFIED",
        "ENRICHED",
        "NEW",
    } else rules.stage
    approval = bool(proposed.requires_human_approval or rules.requires_human_approval)
    reason = rules.approval_reason or proposed.approval_reason
    if rules.requires_human_approval:
        approval = True
        reason = rules.approval_reason
    return proposed.model_copy(
        update={
            "stage": stage,
            "requires_human_approval": approval,
            "approval_reason": reason if approval else None,
            "injection_detected": False,
        }
    )


def _first_name(profile: dict[str, Any]) -> str:
    name = str(profile.get("name") or "").strip()
    return name.split()[0] if name else "there"


def _company(profile: dict[str, Any]) -> str:
    return str(profile.get("company") or "").strip() or "your team"


def _role(profile: dict[str, Any]) -> str:
    return str(profile.get("role") or "").strip() or "operator"


def render_outreach(profile: dict[str, Any], angle: str) -> str:
    first = _first_name(profile)
    company = _company(profile)
    role = _role(profile)
    if angle not in ANGLES:
        angle = ANGLES[0]
    if angle == "direct_value":
        return (
            f"{first}, running {company} as {role} usually means hours lost chasing vendors by text. "
            "We turn that into one thread with a clear owner. Want the 2-minute walkthrough?"
        )
    if angle == "social_proof":
        return (
            f"{first}, a portfolio like {company} booked after a vendor replied in 3 days. "
            "Should I send that same one-pager?"
        )
    if angle == "micro_question":
        return f"{first}, is vendor delay the bottleneck at {company} this month?"
    return (
        f"{first}, I will close the file on {company} unless a short call is useful. "
        "Reply yes and I will send times."
    )


def render_objection(profile: dict[str, Any], history: str) -> str:
    first = _first_name(profile)
    company = _company(profile)
    text = (history or "").lower()
    if any(token in text for token in ("expensive", "price", "discount", "cost", "cheaper", "budget")):
        return (
            f"{first}, {company} stays on the published rate card, and we do not change commercial terms in chat. "
            "The useful comparison is response time on a repair thread. Want the one-page comparison?"
        )
    if any(token in text for token in ("furious", "angry", "ridiculous", "unacceptable", "outraged")):
        return (
            f"{first}, the last note to {company} missed the mark. "
            "A human reviews heated replies before anything else is sent. "
            "Want a person to follow up directly?"
        )
    if any(token in text for token in ("already have", "vendor", "incumbent")):
        return (
            f"{first}, {company} can keep the vendors you already trust. "
            "We only coordinate the thread so replies do not stall. Want the 2-minute walkthrough?"
        )
    return (
        f"{first}, I will answer the {company} question from the published notes, not a guess. "
        "Want the one-page comparison?"
    )


def render_booking(profile: dict[str, Any], link: str) -> str:
    first = _first_name(profile)
    company = _company(profile)
    return f"{first}, your {company} booking link is {link}. Grab any open 15-minute slot."


def deterministic_win(state: dict[str, Any]) -> dict[str, Any]:
    profile = state.get("lead_profile") or {}
    industry = str(profile.get("industry") or profile.get("role") or "general")
    persona = str(profile.get("role") or "operator")
    angle = str(state.get("last_angle_used") or "direct_value")
    outcome = str(state.get("outcome_label") or state.get("stage") or "engaged")
    text = (
        f"For a {persona} in {industry}, angle {angle} preceded {outcome}. "
        "Keep one concrete operating detail and one soft CTA. Do not offer commercial exceptions."
    )
    return {
        "text": text,
        "heuristic": text,
        "angle": angle,
        "persona": persona,
        "industry": industry,
        "outcome": outcome,
        "lead_id": state.get("lead_id"),
    }


def deterministic_failure_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[str]] = {
        "early_opt_out": [],
        "late_opt_out": [],
        "breakup_ignored": [],
        "silent_ghost": [],
        "price_friction": [],
    }
    proposals = {
        "early_opt_out": "Open with the portfolio name and one easy no. Do not stack a second question.",
        "late_opt_out": "Stop the chase before a fourth cold touch when earlier notes got silence.",
        "breakup_ignored": "Keep the breakup note to two short sentences and do not add a new pitch.",
        "silent_ghost": "Move to the micro-question sooner instead of repeating the value paragraph.",
        "price_friction": "Answer price from the rate-card battlecard and escalate exceptions. Never invent a discount.",
    }
    targets = {
        "early_opt_out": "outreach_drafter",
        "late_opt_out": "dispatch_and_schedule",
        "breakup_ignored": "outreach_drafter",
        "silent_ghost": "outreach_drafter",
        "price_friction": "objection_handler",
    }
    for record in records:
        lead_id = str(record.get("lead_id") or "")
        stage = str(record.get("stage") or "")
        touches = int(record.get("touchpoint_count") or 0)
        angle = str(record.get("last_angle_used") or "")
        inbound = str(record.get("inbound_text") or "").lower()
        if any(token in inbound for token in ("price", "expensive", "discount", "cheaper")):
            buckets["price_friction"].append(lead_id)
        if stage == "UNSUBSCRIBED" and touches <= 1:
            buckets["early_opt_out"].append(lead_id)
        elif stage == "UNSUBSCRIBED":
            buckets["late_opt_out"].append(lead_id)
        elif stage == "GHOSTING" and angle == "breakup_note":
            buckets["breakup_ignored"].append(lead_id)
        elif stage == "GHOSTING":
            buckets["silent_ghost"].append(lead_id)
    clusters = []
    improvements = []
    for key, lead_ids in buckets.items():
        if not lead_ids:
            continue
        clusters.append(
            {
                "pattern": key,
                "count": len(lead_ids),
                "lead_ids": lead_ids,
                "proposal": proposals[key],
            }
        )
        improvements.append({"target": targets[key], "change": proposals[key]})
    return {"clusters": clusters, "prompt_improvements": improvements, "source": "deterministic"}


class MockChaseLLM:
    """Deterministic classifier and drafter. No network."""

    def classify(self, state: dict[str, Any]) -> IntentClassification:
        return classify_by_rules(state)

    def draft(self, request: DraftRequest) -> str:
        if request.mode == "booking":
            return render_booking(request.lead_profile, request.booking_link or "")
        if request.mode == "objection":
            return render_objection(request.lead_profile, request.history_snippet)
        return render_outreach(request.lead_profile, request.angle)

    def analyze_failures(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return deterministic_failure_analysis(records)

    def summarize_win(self, state: dict[str, Any]) -> dict[str, Any]:
        return deterministic_win(state)


class ScriptedChaseLLM:
    """Test double: scripted drafts, rule-based classification."""

    def __init__(self, drafts: list[str], inner: MockChaseLLM | None = None) -> None:
        if not drafts:
            raise ValueError("ScriptedChaseLLM requires at least one draft")
        self._drafts = list(drafts)
        self._index = 0
        self.calls = 0
        self._inner = inner or MockChaseLLM()

    def classify(self, state: dict[str, Any]) -> IntentClassification:
        return self._inner.classify(state)

    def draft(self, request: DraftRequest) -> str:
        self.calls += 1
        index = min(self._index, len(self._drafts) - 1)
        self._index += 1
        return self._drafts[index]

    def analyze_failures(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._inner.analyze_failures(records)

    def summarize_win(self, state: dict[str, Any]) -> dict[str, Any]:
        return self._inner.summarize_win(state)


class RealChaseLLM:
    """Structured-output wrapper around LangChain chat models."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def classify(self, state: dict[str, Any]) -> IntentClassification:
        payload = {
            "stage": state.get("stage"),
            "profile": state.get("lead_profile"),
            "latest_human": latest_human_text(state),
            "scheduled_follow_up": is_scheduled_followup(state),
        }
        structured = self._model.with_structured_output(IntentClassification)
        result = structured.invoke(
            [
                SystemMessage(content=CLASSIFY_SYSTEM),
                HumanMessage(content=str(payload)),
            ]
        )
        if isinstance(result, IntentClassification):
            return result
        return IntentClassification.model_validate(result)

    def draft(self, request: DraftRequest) -> str:
        structured = self._model.with_structured_output(DraftOutput)
        result = structured.invoke(
            [
                SystemMessage(content=DRAFT_SYSTEM),
                HumanMessage(
                    content=str(
                        {
                            "mode": request.mode,
                            "angle": request.angle,
                            "profile": request.lead_profile,
                            "critic_feedback": request.critic_feedback,
                            "battlecard": request.battlecard[:2000],
                            "booking_link": request.booking_link,
                            "history": request.history_snippet[:1500],
                            "winning_tactics": request.winning_tactics[:3],
                        }
                    )
                ),
            ]
        )
        if isinstance(result, DraftOutput):
            return result.message.strip()
        return DraftOutput.model_validate(result).message.strip()

    def analyze_failures(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            structured = self._model.with_structured_output(ReflectionAnalysis)
            result = structured.invoke(
                [
                    SystemMessage(content=REFLECT_SYSTEM),
                    HumanMessage(content=str(records)[:8000]),
                ]
            )
            if isinstance(result, ReflectionAnalysis):
                data = result.model_dump()
            else:
                data = ReflectionAnalysis.model_validate(result).model_dump()
            data["source"] = "model"
            if not data.get("clusters"):
                return deterministic_failure_analysis(records)
            return data
        except Exception:
            logger.exception("reflection model failed; using deterministic clusters")
            return deterministic_failure_analysis(records)

    def summarize_win(self, state: dict[str, Any]) -> dict[str, Any]:
        fallback = deterministic_win(state)
        try:
            structured = self._model.with_structured_output(WinHeuristic)
            result = structured.invoke(
                [
                    SystemMessage(content=WIN_SYSTEM),
                    HumanMessage(content=str({
                        "profile": state.get("lead_profile"),
                        "angle": state.get("last_angle_used"),
                        "outcome": state.get("outcome_label") or state.get("stage"),
                        "draft": (state.get("draft_message") or "")[:500],
                    })),
                ]
            )
            parsed = result if isinstance(result, WinHeuristic) else WinHeuristic.model_validate(result)
            data = fallback | parsed.model_dump()
            data["text"] = parsed.text or fallback["text"]
            return data
        except Exception:
            logger.exception("win summary model failed; using deterministic heuristic")
            return fallback


def build_chat_model(settings: Settings | None = None) -> Any | None:
    settings = settings or get_settings()
    if settings.openai_api_key.strip():
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    if settings.anthropic_api_key.strip():
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )
    return None


def build_llm(settings: Settings | None = None) -> ChaseLLM:
    settings = settings or get_settings()
    model = None
    if settings.llm_provider != "mock":
        try:
            model = build_chat_model(settings)
        except Exception:
            logger.exception("chat model import failed; using the deterministic mock")
            model = None
    if model is None:
        return MockChaseLLM()
    return RealChaseLLM(model)
