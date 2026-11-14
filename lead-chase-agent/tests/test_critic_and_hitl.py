"""Rubric retries and the human approval interrupt."""

from __future__ import annotations

import json

from langgraph.types import Command

from src.agent.critic import evaluate_draft
from src.agent.graph import build_graph, initial_state, make_memory_store, thread_config
from src.agent.llm import MockChaseLLM, ScriptedChaseLLM, render_booking, render_objection, render_outreach
from src.agent.state import ANGLES
from src.tools.crm import list_touchpoints
from tests.support import PROFILE

BAD_DRAFT = (
    "Hope this finds you well. Just checking in on things. "
    "Can we chat tomorrow? Also book a call and reply with times. "
    "I can offer a 20% discount if you sign this week."
)


def _graph(llm):
    from langgraph.checkpoint.memory import InMemorySaver

    return build_graph(checkpointer=InMemorySaver(), store=make_memory_store(), llm=llm)


def _view(result):
    if isinstance(result, dict):
        data = dict(result)
        data.pop("__interrupt__", None)
        return data
    return dict(getattr(result, "value", {}) or {})


def _interrupts(result):
    if isinstance(result, dict):
        return list(result.get("__interrupt__") or ())
    return list(getattr(result, "interrupts", ()) or ())


def _outbound(lead_id: str) -> list[dict]:
    return [row for row in list_touchpoints(lead_id) if row["direction"] == "outbound"]


def test_rubric_rejects_filler_multi_cta_and_discount() -> None:
    ok, feedback = evaluate_draft(BAD_DRAFT, {"lead_profile": PROFILE, "messages": []})
    assert ok is False
    lowered = feedback.lower()
    assert "filler" in lowered
    assert "cta" in lowered
    assert "discount" in lowered or "pricing" in lowered


def test_default_templates_pass_the_rubric() -> None:
    state = {"lead_profile": PROFILE, "messages": []}
    link = "https://cal.example.com/book/lead"
    drafts = [render_outreach(PROFILE, angle) for angle in ANGLES]
    drafts.append(render_objection(PROFILE, "This is too expensive. Can you do better on price?"))
    drafts.append(render_objection(PROFILE, "I am furious about the last note."))
    drafts.append(render_booking(PROFILE, link))
    for draft in drafts:
        ok, feedback = evaluate_draft(draft, state)
        assert ok, feedback


def test_critic_retries_then_passes() -> None:
    good = render_outreach(PROFILE, "direct_value")
    scripted = ScriptedChaseLLM([BAD_DRAFT, good])
    graph = _graph(scripted)
    lead_id = "critic-pass"
    state = _view(graph.invoke(initial_state(lead_id, **PROFILE), thread_config(lead_id)))
    assert scripted.calls == 2
    assert state["critic_retries"] == 1
    assert state["draft_message"] == good
    assert state["touchpoint_count"] == 1
    assert _outbound(lead_id)[0]["body"] == good
    assert "just checking in" not in state["draft_message"].lower()


def test_critic_exhaustion_interrupts_for_a_human() -> None:
    scripted = ScriptedChaseLLM([BAD_DRAFT, BAD_DRAFT, BAD_DRAFT])
    graph = _graph(scripted)
    lead_id = "critic-fail"
    config = thread_config(lead_id)
    result = graph.invoke(initial_state(lead_id, **PROFILE), config)
    state = _view(result)
    assert scripted.calls == 3
    assert state["critic_retries"] == 2
    assert state["requires_human_approval"] is True
    assert state["approval_reason"] == "critic_failed"
    assert _interrupts(result)
    assert _outbound(lead_id) == []

    rejected = _view(graph.invoke(Command(resume={"action": "reject"}), config))
    assert rejected["outcome_label"] == "human_rejected"
    assert _outbound(lead_id) == []


def test_angry_reply_interrupts_until_approved() -> None:
    graph = _graph(MockChaseLLM())
    lead_id = "hitl-angry"
    config = thread_config(lead_id)
    result = graph.invoke(
        initial_state(lead_id, message="I am furious about the last note.", **PROFILE),
        config,
    )
    state = _view(result)
    interrupts = _interrupts(result)
    assert interrupts
    assert state["requires_human_approval"] is True
    assert state["approval_reason"] == "angry_sentiment"
    payload = getattr(interrupts[0], "value", {})
    assert payload["draft_message"]
    assert "discount" not in payload["draft_message"].lower()
    assert _outbound(lead_id) == []

    approved = _view(graph.invoke(Command(resume={"action": "approve"}), config))
    assert approved["touchpoint_count"] == 1
    sent = _outbound(lead_id)
    assert len(sent) == 1
    assert "Northwind" in sent[0]["body"]
    assert json.loads(sent[0]["payload_json"])["to"] == PROFILE["email"]


def test_operator_edit_is_what_gets_sent() -> None:
    graph = _graph(MockChaseLLM())
    lead_id = "hitl-edit"
    config = thread_config(lead_id)
    graph.invoke(
        initial_state(lead_id, message="I am furious about the last note.", **PROFILE),
        config,
    )
    edited = "Alex, a human at Northwind will take the furious note from here. Want a person to call?"
    state = _view(graph.invoke(Command(resume={"action": "edit", "draft": edited}), config))
    assert state["draft_message"] == edited
    assert _outbound(lead_id)[0]["body"] == edited


def test_operator_reject_sends_nothing() -> None:
    graph = _graph(MockChaseLLM())
    lead_id = "hitl-reject"
    config = thread_config(lead_id)
    graph.invoke(
        initial_state(lead_id, message="We are an enterprise procurement team. Send details.", **PROFILE),
        config,
    )
    state = _view(graph.invoke(Command(resume={"action": "reject"}), config))
    assert state["outcome_label"] == "human_rejected"
    assert state["approval_reason"] == "rejected"
    assert _outbound(lead_id) == []


def test_enterprise_vip_requires_approval_before_send() -> None:
    graph = _graph(MockChaseLLM())
    lead_id = "hitl-vip"
    result = graph.invoke(
        initial_state(
            lead_id,
            message="Our enterprise procurement team wants a look at the workflow.",
            **PROFILE,
        ),
        thread_config(lead_id),
    )
    state = _view(result)
    assert _interrupts(result)
    assert state["approval_reason"] == "enterprise_vip"
    assert state["stage"] == "ENGAGED"
    draft = state["draft_message"].lower()
    assert "discount" not in draft
    assert "$" not in draft
    assert _outbound(lead_id) == []
