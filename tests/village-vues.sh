#!/usr/bin/env bash
set -u
PORT=9250
PROF="/tmp/chrome-vues-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" 2>/dev/null; }
trap cleanup EXIT
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --autoplay-policy=no-user-gesture-required --window-size=1600,1000 \
  "http://127.0.0.1:8099/index.html" >/tmp/vues-chrome.log 2>&1 &
sleep 9
timeout 140 node ~/donjon-vr/tests/village-vues.js $PORT
echo "--- chrome tué par le trap ---"
