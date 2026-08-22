#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════
#  SERVEUR DU POSEUR (donjon-plan) — sert la page ET reçoit des fichiers 3D.
#
#  Le serveur simple (http.server) ne fait que LIRE. Ici on ajoute une porte
#  pour IMPORTER un modèle 3D pris ailleurs (glb, gltf, vrm, fbx, obj, png/jpg).
#  Le fichier arrive de la page, on l'écrit dans assets/importes/, et on répond
#  le chemin à réutiliser dans le jeu.
#
#  Lancer :  cd ~/donjon-vr && python3 poseur-serveur.py
#  Puis ouvrir :  http://127.0.0.1:8777/donjon-plan.html
# ══════════════════════════════════════════════════════════════════════
import http.server, socketserver, os, json, re

PORT = 8777
RACINE = os.path.expanduser('~/donjon-vr')
IMPORTES = os.path.join(RACINE, 'assets', 'importes')
os.makedirs(IMPORTES, exist_ok=True)
EXT_OK = {'.glb', '.gltf', '.vrm', '.fbx', '.obj', '.png', '.jpg', '.jpeg', '.hdr', '.bin'}

class Poseur(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RACINE, **k)

    def end_headers(self):
        # pas de cache (on voit toujours la dernière version) + import autorisé
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, *a): pass

    def do_GET(self):
        # liste des modèles déjà importés (pour les proposer dans la page)
        if self.path.startswith('/importes'):
            fichiers = ['assets/importes/' + f for f in sorted(os.listdir(IMPORTES))
                        if os.path.splitext(f)[1].lower() in EXT_OK]
            corps = json.dumps({'fichiers': fichiers}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(corps))); self.end_headers()
            self.wfile.write(corps); return
        super().do_GET()

    def do_POST(self):
        if self.path != '/importer':
            self.send_error(404); return
        ctype = self.headers.get('Content-Type', '')
        m = re.search(r'boundary=([^;]+)', ctype)
        if 'multipart/form-data' not in ctype or not m:
            return self._rep(400, {'erreur': 'envoie un fichier (multipart/form-data)'})
        # Le module cgi n'existe plus (Python 3.13+). On découpe le multipart à la main.
        longueur = int(self.headers.get('Content-Length') or 0)
        if longueur > 90 * 1024 * 1024:
            return self._rep(400, {'erreur': 'fichier trop gros (plus de 80 Mo)'})
        brut = self.rfile.read(longueur)
        sep = ('--' + m.group(1)).encode()
        parties = brut.split(sep)
        nom = None; data = None
        for p in parties:
            if b'filename=' not in p: continue
            entete, _, corps = p.partition(b'\r\n\r\n')
            fn = re.search(rb'filename="([^"]*)"', entete)
            if not fn or not fn.group(1): continue
            nom = os.path.basename(fn.group(1).decode('utf-8', 'replace'))
            data = corps.rstrip(b'\r\n-')               # retire la fin du bloc multipart
            break
        if not nom or data is None:
            return self._rep(400, {'erreur': 'aucun fichier reçu'})
        nom = re.sub(r'[^A-Za-z0-9._-]', '_', nom)      # nom propre, jamais de chemin traversant
        ext = os.path.splitext(nom)[1].lower()
        if ext not in EXT_OK:
            return self._rep(400, {'erreur': 'type refusé : ' + ext + ' (attendus : ' + ', '.join(sorted(EXT_OK)) + ')'})
        dest = os.path.join(IMPORTES, nom)
        with open(dest, 'wb') as f: f.write(data)
        chemin = 'assets/importes/' + nom
        print('IMPORTÉ :', chemin, '(' + str(len(data)//1024) + ' Ko)')
        self._rep(200, {'ok': True, 'chemin': chemin, 'taille_ko': len(data)//1024})

    def _rep(self, code, obj):
        corps = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(corps))); self.end_headers()
        self.wfile.write(corps)

socketserver.TCPServer.allow_reuse_address = True
print('POSEUR sur http://127.0.0.1:%d/donjon-plan.html' % PORT)
print('  importe les modèles 3D dans : assets/importes/')
socketserver.TCPServer(('127.0.0.1', PORT), Poseur).serve_forever()
