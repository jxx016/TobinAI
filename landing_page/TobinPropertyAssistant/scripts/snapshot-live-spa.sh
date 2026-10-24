#!/usr/bin/env bash
# Download the current cool-cannoli static files so a function deploy
# can republish the same SPA. Does not deploy and does not call Netlify.
set -euo pipefail

DEST="${1:-/tmp/cool-cannoli-publish}"
ORIGIN="${SPA_ORIGIN:-https://cool-cannoli-68cac9.netlify.app}"

rm -rf "$DEST"
mkdir -p "$DEST"

python3 - "$DEST" "$ORIGIN" << 'PY'
import pathlib, re, sys, urllib.request

dest = pathlib.Path(sys.argv[1])
origin = sys.argv[2].rstrip("/")

def fetch(url: str) -> tuple[bytes, str]:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read(), resp.headers.get("content-type", "")

index, index_type = fetch(origin + "/")
if "text/html" not in index_type or b'id="root"' not in index:
    raise SystemExit(f"unexpected homepage ({index_type}, {len(index)} bytes)")
(dest / "index.html").write_bytes(index)

html = index.decode("utf-8", "replace")
paths = []
for match in re.findall(r'(?:src|href)="(/[^"]+)"', html):
    path = match.split("?", 1)[0]
    if path.startswith("//") or path in paths:
        continue
    paths.append(path)

for path in paths:
    data, ctype = fetch(origin + path)
    if data == index or "text/html" in ctype:
        print(f"skip SPA fallback {path} ({ctype}, {len(data)} bytes)")
        continue
    out = dest / path.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"saved {path} {len(data)} bytes {ctype}")

js_files = list((dest / "assets").glob("*.js")) if (dest / "assets").exists() else []
if not js_files:
    raise SystemExit("snapshot has no JS bundle; refusing an empty SPA")
bundle = "\n".join(p.read_text("utf-8", "replace") for p in js_files)
if "/.netlify/functions/demo-request" not in bundle:
    raise SystemExit("bundle does not post to /.netlify/functions/demo-request")

(dest / "_redirects").write_text("/*    /index.html   200\n")
print("wrote _redirects")
print(f"publish dir {dest}")
PY

find "$DEST" -type f -printf '%p %s\n' | sort
