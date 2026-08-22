#!/usr/bin/env python3
# chat-traduction.py — serveur local de traduction du chat (port 8766).
#
# Responsabilité SÉPARÉE du world builder : le chat parle à ce petit serveur,
# qui possède la clé DeepSeek (env DEEPSEEK_API_KEY, jamais dans le code ni
# dans le navigateur). Si la clé est absente, il répond 501 et le jeu garde
# le français (le navigateur a aussi son petit dictionnaire de secours).
# Multi-threadé : un client qui meurt en plein transfert ne fige pas le serveur
# (leçon payée le 22/08 avec serveur-nocache mono-thread).
#
# Lancement :  DEEPSEEK_API_KEY=... python3 chat-traduction.py
# Test :       curl -s -X POST http://127.0.0.1:8766/traduire \
#                -H 'Content-Type: application/json' \
#                -d '{"text":"Bonjour, vous allez bien ?","source":"fr","target":"ja"}'
import http.server
import json
import os
import socketserver
import urllib.error
import urllib.request

PORT = 8766
URL_DEEPSEEK = "https://api.deepseek.com/chat/completions"
MODELE = "deepseek-chat"

PROMPT_SYSTEME = (
    "Tu traduis du français vers un japonais naturel et conversationnel, comme "
    "le parlerait un personnage d'anime. Garde le sens, le ton, les émotions "
    "et les noms propres. N'ajoute RIEN d'autre : réponds uniquement avec la "
    "traduction, sans guillemets ni préfixe."
)


def traduire(texte: str) -> str:
    cle = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not cle:
        raise OSError("clé DEEPSEEK_API_KEY absente")
    corps = json.dumps({
        "model": MODELE,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": "Traduis en japonais : " + texte},
        ],
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        URL_DEEPSEEK, data=corps,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cle},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            reponse = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise OSError("DeepSeek HTTP %s : %s" % (e.code, e.read()[:200]))
    except Exception as e:
        raise OSError("DeepSeek injoignable : %s" % e)
    try:
        return reponse["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise OSError("réponse DeepSeek inattendue")


class H(http.server.BaseHTTPRequestHandler):
    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/traduire":
            self._json(404, {"erreur": "route inconnue : " + self.path})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            corps = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"erreur": "JSON invalide"})
            return
        texte = (corps.get("text") or "").strip()
        if not texte:
            self._json(400, {"erreur": "texte vide"})
            return
        try:
            traduction = traduire(texte)
        except OSError as e:
            self._json(501, {"erreur": str(e)})
            return
        self._json(200, {"traduction": traduction, "source": "deepseek"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    print("Serveur de traduction sur http://127.0.0.1:%d" % PORT)
    socketserver.ThreadingTCPServer(("", PORT), H).serve_forever()
