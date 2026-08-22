#!/usr/bin/env bash
# Capture avec le HUD visible (pour juger le système UI) — un seul chrome, tué à la fin.
set -u
HASH="${1:-#village}"
OUT="${2:-/tmp/capture-hud.png}"
PORT=9250
PROF="/tmp/chrome-hud-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" /tmp/cdp-hud.js 2>/dev/null; }
trap cleanup EXIT
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --window-size=1600,1000 "http://127.0.0.1:8099/index.html" >/tmp/hud-chrome.log 2>&1 &
sleep 9
sed "s/9222/$PORT/g" ~/donjon-vr/cdp-jouer.js > /tmp/cdp-hud.js
TS=$(date +%s)
timeout 80 node /tmp/cdp-hud.js '[
  {"nav":"?t='"$TS"''"$HASH"'"},
  {"wait":22000},
  {"eval":"var b=document.getElementById(\"jouer\");(b&&!b.disabled)?(b.click(),\"clic\"):(\"etat=\"+window.D.etat)"},
  {"wait":10000},
  {"eval":"(function(){var j=window.D.joueur;j.tangage=0.10;if(window.D.etat===\"jeu\"&&window.D.basculerVue)window.D.basculerVue();return \"vue 3e\";})()"},
  {"wait":1000},
  {"shot":"'"$OUT"'"}
]' 2>&1 | tail -4
echo "--- chrome tué par le trap ---"
