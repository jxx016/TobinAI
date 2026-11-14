"""Force the sandbox before any application module reads settings."""

from __future__ import annotations

import os

os.environ["MOCK_EXTERNAL_SERVICES"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CHECKPOINT_DATABASE_URL"] = ""
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
for _secret in (
    "TAVILY_API_KEY",
    "FIRECRAWL_API_KEY",
    "RESEND_API_KEY",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_ACCOUNT_SID",
    "CALCOM_API_KEY",
):
    os.environ[_secret] = ""

import pytest

from src.agent.graph import build_graph, make_memory_store, reset_graph
from src.config import reset_settings

reset_settings()


@pytest.fixture(autouse=True)
def _reset_process_graph():
    reset_settings()
    reset_graph()
    yield
    reset_graph()


@pytest.fixture
def graph():
    from langgraph.checkpoint.memory import InMemorySaver

    return build_graph(checkpointer=InMemorySaver(), store=make_memory_store())
