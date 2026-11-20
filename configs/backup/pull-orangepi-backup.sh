#!/bin/sh
# Pull nightly Orange Pi backups onto the Deck (LAN first, Tailscale fallback).
set -eu
DEST="$HOME/Backups/orangepi"
mkdir -p "$DEST"
for HOST in 192.168.18.28 100.81.251.12; do
  if rsync -a --timeout=30 -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
       "fritz@$HOST:/var/backups/pi/" "$DEST/"; then
    # Keep the newest 30 on the Deck.
    ls -1t "$DEST"/pi-*.tar.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
    echo "pulled from $HOST"; exit 0
  fi
done
echo "Orange Pi unreachable" >&2; exit 1
