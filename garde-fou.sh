#!/usr/bin/env bash
# ============================================================
#  CIRCUIT QUALITÉ DE KOTOAGE — les portes à franchir AVANT un commit.
#  Une porte qui refuse fait son travail. Rien ne part si une porte est ROUGE.
#  Gouvernance par projet (demande de Patrick 21/08).
#
#  Usage :  bash garde-fou.sh [capture1.png capture2.png ...]
#  Les captures passées sont soumises à la Porte 3 (œil Gemini).
# ============================================================
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
ROUGE=0
echo "═══════════ CIRCUIT KOTOAGE ═══════════"

# ── PORTE 1 : syntaxe + invariants ──────────────────────────
echo "── Porte 1 : syntaxe & invariants (test-jeu.js)"
R=$(node "$DIR/test-jeu.js" 2>&1 | tail -1); echo "   $R"
echo "$R" | grep -q "0 échoués" || { echo "   ⛔ PORTE 1 FERMÉE — on ne commit pas."; ROUGE=1; }

# ── PORTE 2 : comportement (jeu piloté) ─────────────────────
echo "── Porte 2 : comportement (tests/run.sh)"
if [ -f "$DIR/tests/run.sh" ]; then
  bash "$DIR/tests/run.sh" 2>&1 | tail -6
else
  echo "   (tests/run.sh absent)"
fi

# ── PORTE 3 : œil visuel externe (Gemini) ───────────────────
if [ -f "$HOME/.gemini-key" ]; then
  echo "── Porte 3 : œil visuel (Gemini)"
  for img in "$@"; do
    if [ -f "$img" ]; then
      echo "   • $(basename "$img") :"
      python3 "$DIR/gemini-critique.py" "$img" 2>&1 | sed 's/^/     /'
    fi
  done
  [ $# -eq 0 ] && echo "   (aucune capture fournie — passe des .png en argument)"
else
  echo "── Porte 3 : INACTIVE (dépose la clé : echo 'CLE' > ~/.gemini-key && chmod 600 ~/.gemini-key)"
fi

# ── PORTE 4 : validation Patrick (humaine) ──────────────────
echo "── Porte 4 : la validation de Patrick (son œil décide)."
echo "═══════════════════════════════════════"
[ $ROUGE -eq 0 ] && echo "Portes automatiques : VERTES. À soumettre à Patrick." || { echo "Une porte est ROUGE : NE PAS committer."; exit 1; }
