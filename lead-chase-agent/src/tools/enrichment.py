"""Web enrichment shaped like Tavily / Firecrawl, with a realistic mock."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from src.config import get_settings

logger = logging.getLogger(__name__)


def enrich_lead_impl(name: str, company: str, role: str = "", industry: str = "") -> dict:
    """Return public context for a lead. Mock mode never leaves the process."""

    settings = get_settings()
    if settings.mock_external_services:
        resolved_industry = industry.strip() or "property-management"
        who = role.strip() or "manager"
        org = company.strip() or "the company"
        summary = (
            f"{org} appears to run multi-site property operations coordinated by a {who}. "
            "Public pages mention vendor scheduling and after-hours repairs."
        )
        return {
            "provider": "mock",
            "industry": resolved_industry,
            "summary": summary,
            "signals": ["multi-site operations", "vendor scheduling", "after-hours repairs"],
            "sources": [],
        }

    query = " ".join(part for part in (name, role, company, "property maintenance") if part).strip()
    if settings.tavily_api_key.strip():
        return _tavily_search(query, industry, settings.tavily_api_key.strip())
    if settings.firecrawl_api_key.strip():
        return _firecrawl_search(query, industry, settings.firecrawl_api_key.strip())
    raise RuntimeError(
        "TAVILY_API_KEY or FIRECRAWL_API_KEY is required when MOCK_EXTERNAL_SERVICES=false"
    )


def _tavily_search(query: str, industry: str, api_key: str) -> dict:
    import httpx

    response = httpx.post(
        "https://api.tavily.com/search",
        json={"api_key": api_key, "query": query, "max_results": 3, "search_depth": "basic"},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") or []
    snippets = [str(item.get("content") or "")[:280] for item in results if item.get("content")]
    titles = [str(item.get("title") or "") for item in results if item.get("title")]
    sources = [str(item.get("url") or "") for item in results if item.get("url")]
    summary = " ".join(snippets)[:800] or "No public snippets returned."
    return {
        "provider": "tavily",
        "industry": industry or "unknown",
        "summary": summary,
        "signals": titles[:5],
        "sources": sources[:5],
    }


def _firecrawl_search(query: str, industry: str, api_key: str) -> dict:
    import httpx

    response = httpx.post(
        "https://api.firecrawl.dev/v1/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query, "limit": 3},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("data") or payload.get("results") or []
    snippets = []
    sources = []
    for item in results:
        text = item.get("markdown") or item.get("description") or item.get("content") or ""
        if text:
            snippets.append(str(text)[:280])
        if item.get("url"):
            sources.append(str(item["url"]))
    summary = " ".join(snippets)[:800] or "No public snippets returned."
    return {
        "provider": "firecrawl",
        "industry": industry or "unknown",
        "summary": summary,
        "signals": snippets[:3],
        "sources": sources[:5],
    }


@tool
def enrich_lead(name: str, company: str, role: str = "", industry: str = "") -> dict:
    """Look up public context for a lead's company and role (Tavily or Firecrawl shape)."""

    logger.info("enrich_lead company=%s mock=%s", company, get_settings().mock_external_services)
    return enrich_lead_impl(name=name, company=company, role=role, industry=industry)
