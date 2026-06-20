#!/usr/bin/env python3
"""
Generate TobinAI promo segments with Gemini Veo 3.1 (Gemini API).

Each Veo generation is ~8 seconds (model limit). Total length = ~8s × number of
segments. This script runs five vertical (9:16) segments (~40s when stitched);
concatenate with ffmpeg when done.

Auth (pick one):
  - Vertex AI: GEMINI_PROJECT_ID, GEMINI_LOCATION, CONFIG_GEMINI_SERVICE_ACCOUNT
    (base64 or JSON service account). Used by default when these are set.
  - Gemini API: GEMINI_API_KEY. Set GEMINI_USE_GEMINI_API=1 to prefer the key
    when both Vertex and key are present.

Usage (from repo root):
  python3 -m venv scripts/.venv && source scripts/.venv/bin/activate
  pip install -r scripts/requirements-veo.txt
  python scripts/generate_veo_tobin_ad.py

Optional:
  python scripts/generate_veo_tobin_ad.py --segment 2   # only segment 2 (1-5)
"""

from __future__ import annotations

import argparse
from typing import Optional, Tuple
import base64
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
import requests

MODEL = "veo-3.1-generate-preview"

# Repo root = parent of scripts/
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "veo_tobin_ad"

SEGMENTS: list[tuple[str, str]] = [
    (
        "01_hook",
        """Vertical 9:16 mobile ad, cinematic but realistic. Pitch black screen; an iPhone lock screen
lights up in darkness. Clock clearly reads 2:14 AM. Loud, annoying default iPhone notification sound.
A text bubble appears: "Hey, the toilet is overflowing!!" from Unit 4B. Bold on-screen caption:
"Sick of tenants calling in the middle of the night?" Slight handheld tension, cool blue phone glow.""",
    ),
    (
        "02_agitation",
        """Vertical 9:16, fast-paced montage: many chat bubbles pop in rapid succession over a blurred
phone UI: "Did you call the plumber?", "Plumber didn't show up", "When is he coming?" Stressed pacing,
quick cuts. Bold caption: "Tired of playing phone tag between angry tenants and busy contractors?"
Chaotic energy, shallow depth of field.""",
    ),
    (
        "03_pivot",
        """Vertical 9:16. Hard wipe transition: screen clears to a calm, minimal product UI with soft
gradient background. TobinAI logo centered, modern sans-serif, trustworthy teal and white palette.
Smooth motion, satisfying transition. Voiceover-style caption: "Meet TobinAI. Your 24/7 automated
maintenance coordinator." Peaceful, premium SaaS aesthetic.""",
    ),
    (
        "04_demo",
        """Vertical 9:16, clean product demo only. Three smartphone screens side by side in frame.
Left: tenant types "AC is broken." Center: TobinAI chat: "Emergency at Unit 2. Can you go?" to HVAC.
Right: contractor replies "On my way." Then Tobin auto-replies to tenant: "HVAC arriving at 3 PM."
Professional, readable UI mockups, smooth motion.""",
    ),
    (
        "05_cta",
        """Vertical 9:16, clean minimal end card. One clean email or notification: "Resolved: AC Fixed.
Cost: $250. Logged to Unit 2." Bold text: "You sleep through the night. We handle the rest."
Final CTA: "Start your 30-day free trial at tobinai.com" with subtle motion. Calm, trustworthy
brand finish.""",
    ),
]


def load_service_account_dict() -> dict:
    raw = os.environ.get("CONFIG_GEMINI_SERVICE_ACCOUNT", "").strip()
    if not raw:
        raise ValueError("CONFIG_GEMINI_SERVICE_ACCOUNT is empty")
    if raw.startswith("{"):
        return json.loads(raw)
    return json.loads(base64.b64decode(raw).decode())


def make_client() -> Tuple[genai.Client, Optional[service_account.Credentials]]:
    load_dotenv(ROOT / ".env")
    project = (os.environ.get("GEMINI_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = (
        os.environ.get("GEMINI_LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    ).strip()
    has_sa = bool(os.environ.get("CONFIG_GEMINI_SERVICE_ACCOUNT", "").strip())
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    prefer_gemini_api = os.environ.get("GEMINI_USE_GEMINI_API", "").lower() in ("1", "true", "yes")

    if prefer_gemini_api and api_key:
        print("Using Gemini API (GEMINI_USE_GEMINI_API=1).")
        return genai.Client(api_key=api_key), None

    if project and has_sa:
        print(f"Using Vertex AI (project={project}, location={location}).")
        info = load_service_account_dict()
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return (
            genai.Client(
                vertexai=True,
                project=project,
                location=location,
                credentials=creds,
            ),
            creds,
        )

    if api_key:
        print("Using Gemini API key.")
        return genai.Client(api_key=api_key), None

    print(
        "Need either CONFIG_GEMINI_SERVICE_ACCOUNT + GEMINI_PROJECT_ID, or GEMINI_API_KEY.",
        file=sys.stderr,
    )
    sys.exit(1)


def save_generated_video(
    client: genai.Client,
    generated,
    out_path: Path,
    vertex_creds: Optional[service_account.Credentials],
) -> None:
    video = generated.video
    if not video:
        raise ValueError("No video in generated result")

    if video.video_bytes:
        out_path.write_bytes(video.video_bytes)
        return

    if not vertex_creds:
        client.files.download(file=video)
        video.save(str(out_path))
        return

    uri = video.uri
    if not uri:
        raise ValueError("Vertex returned no video bytes and no uri")

    if uri.startswith("gs://"):
        from google.cloud import storage

        rest = uri[5:]
        bucket_name, blob_path = rest.split("/", 1)
        storage_client = storage.Client(credentials=vertex_creds)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(str(out_path))
        return

    vertex_creds.refresh(GoogleAuthRequest())
    resp = requests.get(
        uri,
        headers={"Authorization": f"Bearer {vertex_creds.token}"},
        timeout=600,
    )
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


def generate_one(
    client: genai.Client,
    segment_id: str,
    prompt: str,
    vertex_creds: Optional[service_account.Credentials],
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{segment_id}.mp4"

    print(f"Starting Veo: {segment_id} -> {out_path.name}")
    operation = client.models.generate_videos(
        model=MODEL,
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="1080p",
        ),
    )

    while not operation.done:
        print("  Waiting for generation...")
        time.sleep(10)
        operation = client.operations.get(operation)

    if not operation.response or not operation.response.generated_videos:
        print(f"Error: no video in response for {segment_id}", file=sys.stderr)
        sys.exit(2)

    generated = operation.response.generated_videos[0]
    save_generated_video(client, generated, out_path, vertex_creds)
    print(f"Saved {out_path}")
    return out_path


def write_concat_manifest() -> None:
    """Write concat.txt listing only segment files that exist (ffmpeg concat demuxer)."""
    lines: list[str] = []
    for sid, _ in SEGMENTS:
        name = f"{sid}.mp4"
        if (OUT_DIR / name).is_file():
            lines.append(f"file '{name}'")
    if not lines:
        return
    path = OUT_DIR / "concat.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(lines)} file(s)).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TobinAI Veo ad segments.")
    parser.add_argument(
        "--segment",
        type=int,
        choices=range(1, len(SEGMENTS) + 1),
        default=None,
        help="Run only this segment number (1-5). Default: run all five.",
    )
    args = parser.parse_args()

    client, vertex_creds = make_client()

    indices = [args.segment - 1] if args.segment is not None else range(len(SEGMENTS))
    for i in indices:
        seg_id, prompt = SEGMENTS[i]
        generate_one(client, seg_id, prompt, vertex_creds)

    print()
    write_concat_manifest()
    print("Stitch with ffmpeg:")
    print(f"  cd {OUT_DIR}")
    print("  ffmpeg -y -f concat -safe 0 -i concat.txt -c copy tobin_ad_full.mp4")


if __name__ == "__main__":
    main()
