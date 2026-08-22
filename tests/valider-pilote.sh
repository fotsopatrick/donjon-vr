#!/usr/bin/env bash
# Lanceur de la sonde de validation de la zone pilote (perf + 4 ciels).
# Un seul chrome, tué à la fin. Usage : bash tests/valider-pilote.sh
set -u
PORT=9250
PROF="/tmp/chrome-val-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" 2>/dev/null; }
trap cleanup EXIT
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --autoplay-policy=no-user-gesture-required --window-size=1600,1000 \
  "http://127.0.0.1:8099/index.html" >/tmp/val-chrome.log 2>&1 &
sleep 9
timeout 210 node ~/donjon-vr/tests/valider-pilote.js $PORT ~/donjon-vr/tests/captures/sky-preview
echo "--- chrome tué par le trap ---"
