#!/usr/bin/env bash
# Lance la vérification de la route village→donjon (un seul chrome, tué à la fin).
set -u
PORT=9250
PROF="/tmp/chrome-route-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" 2>/dev/null; }
trap cleanup EXIT
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --autoplay-policy=no-user-gesture-required --window-size=1600,1000 \
  "http://127.0.0.1:8099/index.html" >/tmp/route-chrome.log 2>&1 &
sleep 9
timeout 120 node ~/donjon-vr/tests/route-donjon.js $PORT
echo "--- chrome tué par le trap ---"
