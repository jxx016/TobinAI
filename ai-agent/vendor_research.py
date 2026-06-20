import os
import requests
from langchain_core.tools import tool
from db import get_conn
import psycopg2.extras

PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

CATEGORY_SEARCH_TERMS = {
    "hvac": "HVAC heating cooling contractor",
    "plumbing": "plumber plumbing contractor",
    "electrical": "electrician electrical contractor",
    "general": "handyman general contractor",
}


def search_vendors_nearby(category: str, address: str) -> list[dict]:
    """Search Google Places for vendors near a given address."""
    if not PLACES_API_KEY:
        return []

    term = CATEGORY_SEARCH_TERMS.get(category.lower(), "handyman contractor")
    query = f"{term} near {address}"

    resp = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={"query": query, "key": PLACES_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    vendors = []
    for place in data.get("results", [])[:3]:
        # Get phone number via Place Details
        detail_resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place["place_id"],
                "fields": "name,formatted_phone_number,rating",
                "key": PLACES_API_KEY,
            },
            timeout=10,
        )
        detail = detail_resp.json().get("result", {})
        phone = detail.get("formatted_phone_number")

        if phone:
            vendors.append({
                "name": place.get("name"),
                "phone": phone,
                "rating": place.get("rating"),
                "address": place.get("formatted_address"),
                "place_id": place["place_id"],
            })

    return vendors


def save_outreach_candidates(request_id: str, candidates: list[dict], source: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for v in candidates:
                cur.execute(
                    """
                    INSERT INTO vendor_outreach
                      (request_id, vendor_phone, vendor_name, source, place_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (request_id, v.get("phone"), v.get("name"), source, v.get("place_id")),
                )


def get_pending_outreach(request_id: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, vendor_phone, vendor_name
                FROM vendor_outreach
                WHERE request_id = %s AND accepted IS NULL
                ORDER BY id ASC
                """,
                (request_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def mark_vendor_accepted(outreach_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE vendor_outreach
                SET accepted = true, replied_at = NOW()
                WHERE id = %s
                """,
                (outreach_id,),
            )


def mark_vendor_declined(outreach_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE vendor_outreach
                SET accepted = false, replied_at = NOW()
                WHERE id = %s
                """,
                (outreach_id,),
            )
