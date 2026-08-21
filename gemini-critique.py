#!/usr/bin/env python3
# Envoie une capture du jeu à Gemini (vision) et ramène une critique artistique honnête.
# La clé API est lue depuis ~/.gemini-key et n'est JAMAIS affichée ni committée.
# Usage : python3 gemini-critique.py <image.png> ["question précise"]
import sys, os, json, base64, urllib.request, urllib.error

KEYPATH = os.path.expanduser('~/.gemini-key')
if not os.path.exists(KEYPATH):
    print("PAS DE CLÉ : dépose-la avec  echo 'TA_CLE' > ~/.gemini-key && chmod 600 ~/.gemini-key")
    sys.exit(2)
KEY = open(KEYPATH).read().strip()

if len(sys.argv) < 2:
    print("usage: gemini-critique.py <image.png> [question]"); sys.exit(2)
img = sys.argv[1]
prompt = sys.argv[2] if len(sys.argv) > 2 else (
    "Tu es directeur artistique de jeu vidéo, exigeant et honnête. Voici une capture d'un jeu 3D "
    "(donjon / isekai, style anime, personnages VRoid, Three.js). Le joueur trouve le rendu 'horrible'. "
    "Dis CONCRÈTEMENT et sans politesse ce qui cloche : pose et animation des personnages, placement "
    "des éléments (objets dans les murs ?), décors, éclairage, ambiance, composition. Puis donne 3 à 5 "
    "ACTIONS PRÉCISES et réalisables pour que ça rende beaucoup mieux. Va droit au but, en français."
)

mime = 'image/png' if img.lower().endswith('.png') else 'image/jpeg'
data = base64.b64encode(open(img, 'rb').read()).decode()
body = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": data}}]}]}

# gemini-2.0-flash : rapide, gratuit, multimodal
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + KEY
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
try:
    r = urllib.request.urlopen(req, timeout=90)
    resp = json.load(r)
    print(resp['candidates'][0]['content']['parts'][0]['text'])
except urllib.error.HTTPError as e:
    print("ERREUR API", e.code, ":", e.read().decode()[:400])
except Exception as e:
    print("ERREUR :", type(e).__name__, str(e)[:200])
