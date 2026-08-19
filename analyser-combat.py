#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyser-combat.py — envoie un court clip du jeu à Gemini (Google AI Studio)
et imprime sa description du mouvement. Sert à donner des « yeux » à Claude :
tu colles la sortie dans la conversation.

La CLÉ API reste chez toi (variable d'environnement) — le script ne l'écrit
jamais sur le disque, Claude ne la voit jamais.

--- Préparer (une seule fois) ---
1) Clé API gratuite : https://aistudio.google.com  -> bouton "Get API key".
2) Installer le SDK :   pip install google-genai
   (si indisponible :   pip install google-generativeai  -> voir la note en bas)

--- Utiliser ---
   GEMINI_API_KEY="ta_cle" python3 analyser-combat.py clip.mp4
"""
import os, sys, time

def main():
    if len(sys.argv) < 2:
        print("usage: GEMINI_API_KEY=... python3 analyser-combat.py <clip.mp4>")
        sys.exit(2)
    chemin = sys.argv[1]
    if not os.path.exists(chemin):
        print("fichier introuvable :", chemin); sys.exit(2)
    cle = os.environ.get("GEMINI_API_KEY")
    if not cle:
        print("mets ta clé dans GEMINI_API_KEY (elle ne doit jamais être écrite dans un fichier)."); sys.exit(2)

    from google import genai   # SDK google-genai
    client = genai.Client(api_key=cle)

    print("→ envoi du clip…", flush=True)
    f = client.files.upload(file=chemin)
    # la vidéo doit finir d'être traitée côté Google avant l'analyse
    while getattr(f, "state", None) and str(f.state).endswith("PROCESSING"):
        time.sleep(2); f = client.files.get(name=f.name)

    prompt = ("Décris précisément le MOUVEMENT du personnage dans cette vidéo de jeu : "
              "rythme (lent/rapide), amplitude (ample/étriqué), fluidité (fluide/saccadé/raide), "
              "et surtout ce qui cloche par rapport à un combat d'anime style Naruto. "
              "Sois concret et bref, en français, en 6 puces maximum.")

    print("→ analyse par Gemini…\n", flush=True)
    r = client.models.generate_content(
        model="gemini-2.5-flash",      # modèle multimodal (vidéo). Rétrograder en 'gemini-2.0-flash' si besoin.
        contents=[f, prompt])
    print(r.text)

if __name__ == "__main__":
    main()

# NOTE — ancien SDK 'google-generativeai' (si google-genai indisponible) :
#   import google.generativeai as genai
#   genai.configure(api_key=os.environ["GEMINI_API_KEY"])
#   f = genai.upload_file(path)          # attendre f.state.name == 'ACTIVE'
#   m = genai.GenerativeModel("gemini-2.5-flash")
#   print(m.generate_content([f, prompt]).text)
