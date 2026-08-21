#!/usr/bin/env bash
# Capture UNE image du jeu proprement, avec garantie que le Chrome est tué à la fin.
# Règle nomi : un seul chrome, fermé aussitôt (trap EXIT). Usage: bash capture-propre.sh <hash> <sortie.png>
set -u
HASH="${1:-#village}"
OUT="${2:-/tmp/capture.png}"
PORT=9250
PROF="/tmp/chrome-cap-$$"
cleanup(){ pkill -9 -f "user-data-dir=$PROF" 2>/dev/null; rm -rf "$PROF" /tmp/cdp-cap.js 2>/dev/null; }
trap cleanup EXIT

google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --window-size=1600,1000 "http://127.0.0.1:8099/index.html" >/tmp/cap-chrome.log 2>&1 &
sleep 9
sed "s/9222/$PORT/g" ~/donjon-vr/cdp-jouer.js > /tmp/cdp-cap.js
TS=$(date +%s)
timeout 80 node /tmp/cdp-cap.js '[
  {"nav":"?t='"$TS"''"$HASH"'"},
  {"wait":22000},
  {"eval":"var b=document.getElementById(\"jouer\");(b&&!b.disabled&&window.D.etat!==\"jeu\")?(b.click(),\"clic\"):(\"etat=\"+window.D.etat)"},
  {"wait":10000},
  {"eval":"\"etat=\"+window.D.etat"},
  {"eval":"(function(){var m=window.D.renderer.domElement;document.querySelectorAll(\"canvas\").forEach(c=>c.style.display=(c===m)?\"\":\"none\");var s=document.createElement(\"style\");s.textContent=\"#coeurs,#jauge-energie,#esprit,#msg,#ath,#viseur,#ecoute,#pouvoirs,.coin,#etage,#combo,#cle,#saisie{display:none!important}\";document.head.appendChild(s);[].forEach.call(document.querySelectorAll(\"body>div,body>span\"),function(d){if(/i\\/s|appels|tri|Vue |TAGE/.test(d.textContent||\"\"))d.style.display=\"none\";});var j=window.D.joueur;j.tangage=0.12;if(window.D.etat===\"jeu\"&&window.D.basculerVue)window.D.basculerVue();return \"hud off\";})()"},
  {"wait":1000},
  {"shot":"'"$OUT"'"}
]' 2>&1 | tail -4
echo "--- chrome sera tué par le trap ---"
