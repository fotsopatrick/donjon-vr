#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test du co-maître de jeu WebMCP (assistantWebmcp) branché sur la voix du
monde via traiterChat. Vérifie le COMPORTEMENT sans Chrome : extraction de la
fonction depuis index.html, pont factice, assertions sur les actions.
Principe Tour/Slime : jamais de cadeau — l'épreuve se surmonte, la force se
débloque. Le co-maître ne distribue ni potion ni épée."""
import re, os, sys, subprocess

INDEX = "/home/orel/donjon-vr/index.html"
JS = "/tmp/opencode/assistant-webmcp.js"

html = open(INDEX, encoding="utf-8").read()
if "function assistantWebmcp" not in html:
    sys.exit("FONCTION MANQUANTE dans index.html")

# extraire la fonction pour la tester en isolation
m = re.search(r"function assistantWebmcp\(t\)\{.*?\n\}\n", html, re.S)
if not m:
    sys.exit("EXTRACTION ÉCHOUÉE de assistantWebmcp")
fn = m.group(0)

def run(pont_ok, message):
    """exécute assistantWebmcp(message) avec un pont factice optionnel."""
    doc_decl = ("globalThis.document = {modelContext: {registerTool(){return true;}}, modelContextFake:true};"
                if pont_ok else "globalThis.document = {};")
    pont = ""
    if pont_ok:
        pont = """
            var window = globalThis;
            window.KOTOAGE_WEBMCP = {creerControleurWebMCP(){return [];}};
            window.__webmcpConnexion = {
                monte(){ window.__actions.push('monte'); return true; },
                dire(m){ window.__actions.push('dire:'+m); },
                joueur:{ x:1, z:1, vie:6, epee:true },
            };
            window.__actions = [];
        """
    guard_invoke = ""
    return subprocess.run(
        ["node", "--input-type=module", "-e",
         f'{doc_decl}\n'
         'globalThis.window = globalThis;\n'
         'globalThis.__webmcpConnexion=null;\n'
         f'{pont}\n'
         f'const T=1, niveau=3, joueur={{x:1,z:0}};\n'
         f'function traiterChat(){{}}\n'
         f'{fn}\n'
         f'const r = assistantWebmcp("{message}");\n'
         f'console.log(JSON.stringify({{r, actions: window.__actions||null}}));'
         ],
        capture_output=True, text=True)

def norm(out):
    return out.stdout.strip().splitlines()[-1]

fails = 0
def verifie(nom, cond):
    global fails
    print(("OK  " if cond else "KO  ") + nom)
    if not cond: fails += 1

# 1) sans pont WebMCP : il ne fait rien, ne casse pas, retourne false
out = run(False, "je veux un defi")
verifie("sans pont -> retourne false", '"r":false' in norm(out))

# 2) avec pont : "un defi" fait surgir un ennemi (monte) et annonce
out = run(True, "je veux un defi")
r = norm(out)
verifie("avec pont -> retourne true", '"r":true' in r)
verifie("avec pont -> invoque monte (épreuve)", '"monte"' in r)
verifie("avec pont -> annonce par la voix du monde (dire)", '"dire:' in r)

# 3) "donne une potion" : le co-maître REFUSE de l'accorder (Slime), pas de bonus vie
out = run(True, "donne une potion")
r = norm(out)
verifie("potion -> retourne true (il répond)", '"r":true' in r)
verifie("potion -> N'OCTROIE pas (aucun monte)", "'monte'" not in r)
verifie("potion -> refuse la gratos", "ne se reçoit pas" in r)

# 4) aucune intention WebMCP -> retourne false (on retombe sur parlerJoueur)
out = run(True, "bonjour à tous")
verifie("phrase banale -> retourne false", '"r":false' in norm(out))

print("\n" + ("TOUS LES TESTS PASSENT" if fails == 0 else f"{fails} ÉCHEC(S)"))
sys.exit(1 if fails else 0)