#!/usr/bin/env bash
# Sonde d'état du village (zone pilote) : erreur JS, état, compteurs de rendu.
set -u
PORT=9250
PROF="/tmp/chrome-etat-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" 2>/dev/null; }
trap cleanup EXIT
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --window-size=1600,1000 "http://127.0.0.1:8099/index.html" >/tmp/etat-chrome.log 2>&1 &
sleep 9
sed "s/9222/$PORT/g" ~/donjon-vr/cdp-jouer.js > /tmp/cdp-etat.js
TS=$(date +%s)
timeout 80 node /tmp/cdp-etat.js '[
  {"nav":"?t='"$TS"'#village"},
  {"wait":22000},
  {"eval":"var b=document.getElementById(\"jouer\");(b&&!b.disabled)?(b.click(),\"clic\"):(\"etat=\"+window.D.etat)"},
  {"wait":10000},
  {"eval":"\"etat=\"+window.D.etat+\" err=\"+(window.__derniereErreur||\"aucune\")"},
  {"eval":"(document.getElementById(\"perf\")||{}).textContent||\"pas de perf\""},
  {"eval":"\"calls=\"+(window.D&&window.D.renderer&&window.D.renderer.info&&window.D.renderer.info.render.calls)"},
  {"eval":"\"lumieres=\"+(function(){var n=0;window.D.scene.traverse(o=>{if(o.isPointLight&&o.intensity>0)n++});return n})()"},
  {"shot":"/tmp/pilote-etat.png"}
]' 2>&1 | tail -10
echo "--- chrome tué par le trap ---"
