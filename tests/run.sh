#!/usr/bin/env bash
# ============================================================
#  Lanceur du système de test rejouable de KOTOAGE.
#  - vérifie le serveur du jeu
#  - lance Chrome headless (profil jetable, port dédié)
#  - joue les cas de comportement + captures (tests/runtime.js)
#  - nettoie
#  Usage : bash tests/run.sh
# ============================================================
set -u
PORT=9247
PROF="/tmp/chrome-tests-$$"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "== 1) tests statiques (syntaxe + invariants) =="
node "$DIR/../test-jeu.js" | tail -1

echo "== 2) serveur du jeu =="
if ! curl -s -o /dev/null http://127.0.0.1:8099/index.html; then
  echo "   Serveur 8099 absent → lance:  (cd ~/donjon-vr && python3 -m http.server 8099 &)"
  exit 2
fi
echo "   OK (8099)"

echo "== 3) tests de comportement (jeu piloté en headless) =="
google-chrome --headless=new --user-data-dir="$PROF" --remote-debugging-port=$PORT \
  --disk-cache-size=1 --autoplay-policy=no-user-gesture-required --window-size=1400,850 \
  "http://127.0.0.1:8099/index.html" > /tmp/chrome-tests.log 2>&1 &
CHROME=$!
sleep 8
node "$DIR/runtime.js" $PORT
CODE=$?
kill $CHROME 2>/dev/null
rm -rf "$PROF" 2>/dev/null
exit $CODE
