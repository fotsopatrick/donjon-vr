#!/usr/bin/env bash
# ============================================================
#  Banc de test rejouable du AI World Builder (P0).
#  1) tests unitaires Python (spec, registre, décomposition, analyse)
#  2) test E2E réel : Blender -> GLB -> registre -> scène -> v2 -> déplacement
#  3) test runtime : world-builder.js dans le jeu (Chrome headless, un seul)
#  Usage : bash world_builder/tests/run.sh
# ============================================================
set -u
ICI="$(cd "$(dirname "$0")" && pwd)"
JEU="$(dirname "$ICI")"
PORT_CDP=9249
PROF="/tmp/chrome-wb-$$"

echo "== 1) tests unitaires =="
python3 "$ICI/test_unit.py" || exit 1

echo "== 2) test E2E (Blender réel, sortie temporaire) =="
python3 "$ICI/test_e2e.py" || exit 1

echo "== 3) serveur du jeu =="
if ! curl -s -o /dev/null http://127.0.0.1:8099/index.html; then
  (cd "$JEU" && setsid nohup python3 -m http.server 8099 --bind 127.0.0.1 \
     >/tmp/donjon-serveur.log 2>&1 </dev/null &) 
  sleep 2
fi
curl -s -o /dev/null http://127.0.0.1:8099/index.html || { echo "   serveur injoignable"; exit 2; }

echo "== 4) test runtime (Chrome headless unique, fermé aussitôt) =="
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT_CDP \
  --disk-cache-size=1 --autoplay-policy=no-user-gesture-required --window-size=1400,850 \
  "http://127.0.0.1:8099/index.html" >/tmp/chrome-wb.log 2>&1 &
CHROME=$!
sleep 9
timeout 70 node "$ICI/runtime-wb.js" $PORT_CDP
CODE=$?
kill -9 "$CHROME" 2>/dev/null
sleep 1
pkill -9 -f "$PROF" 2>/dev/null
rm -rf "$PROF" 2>/dev/null
exit $CODE
