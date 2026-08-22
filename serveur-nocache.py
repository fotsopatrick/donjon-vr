#!/usr/bin/env python3
# Sert le jeu SANS cache : Patrick voit toujours la dernière version (fini les vieux bugs revenus).
# Multi-threadé : si un onglet meurt en plein transfert (Chrome tué pendant un test),
# le serveur ne se fige PAS sur la connexion morte (leçon payée le 22/08 — mono-thread = flaky).
import http.server, socketserver
PORT = 8099
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
print("Serveur no-cache (multi-threadé) sur http://127.0.0.1:%d" % PORT)
socketserver.ThreadingTCPServer(('', PORT), H).serve_forever()
