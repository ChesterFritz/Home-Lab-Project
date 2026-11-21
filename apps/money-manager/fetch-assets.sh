#!/bin/sh
# Download the Money Manager web UI (ExtJS app + images) into ./static.
# These files belong to Realbyte and aren't stored in this repo; they're the same
# files the iPhone app's web page loads from Realbyte's CDN.
set -eu
cd "$(dirname "$0")"
BASE=https://s3-ap-northeast-1.amazonaws.com/realbyteapps.net/pcmanager/v330
mkdir -p static
cp index.html print.html static/
fail=0
while IFS= read -r p; do
  [ -n "$p" ] || continue
  [ -s "static/$p" ] && continue
  mkdir -p "static/$(dirname "$p")"
  if ! curl -fsS --retry 2 -m 60 -o "static/$p.part" "$BASE/$p"; then echo "failed: $p" >&2; fail=1; continue; fi
  mv "static/$p.part" "static/$p"
done < assets.txt
[ "$fail" = 0 ] && echo "assets ready in $(pwd)/static" || { echo "some assets failed; re-run to retry" >&2; exit 1; }
