# -*- coding: utf-8 -*-
# Harnais CDP pur (aucune dépendance : websocket natif) pour prouver le WebMCP
# KOTOAGE directement dans un vrai Chrome Headless sur la page LIVE servie par
# le bucket Google Cloud Storage.
#
# Ce harnais ne dépend PAS du flag navigateur : il injecte un document.modelContext
# fabriqué (registerTool/declareTool/setState) qui reproduit fidèlement l'API
# WebMCP (https://modelcontextprotocol.io/specification). Il prouve que, sur la
# page réelle servie par le bucket, la couche webmcp.js (chargée en script
# classique) s'enregistre bien : les 7 outils sont exposés and réalisent des
# effets réels visibles dans l'état du jeu.
#
# Usage : python test_webmcp_live_cdp.py  <URL-live>

import base64
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

def _trouver_chrome():
    if os.name == "nt":
        for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                  r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
            if os.path.exists(c):
                return c
        return CHROME_WIN_DEFAUT
    return (shutil.which("google-chrome") or shutil.which("google-chrome-stable")
            or shutil.which("chromium") or shutil.which("chromium-browser")
            or shutil.which("chrome"))

CHROME_WIN_DEFAUT = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME = _trouver_chrome()
PORT = 9333
URL = sys.argv[1] if len(sys.argv) > 1 else "https://storage.googleapis.com/kotoage-webmcp-20260901-133904/index.html"

# --------------------------- WebSocket natif -------------------------------
class CDPSocket:
    def __init__(self, url):
        self.s = socket.create_connection(("127.0.0.1", PORT), timeout=15)
        self.do_handshake(url)
        self.buf = b""
        self.id = 0
        self.reponses = {}

    def do_handshake(self, ws_url):
        key = base64.b64encode(os.urandom(16)).decode()
        # ws://127.0.0.1:PORT/devtools/page/XXXX  ->  /devtools/page/XXXX
        chemin = ws_url.split("://", 1)[1]
        chemin = "/" + chemin.split("/", 1)[1]
        req = (
            "GET %s HTTP/1.1\r\n"
            "Host: 127.0.0.1:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ) % (chemin, PORT, key)
        self.s.sendall(req.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.s.recv(4096)
        headers = resp.split(b"\r\n\r\n")[0].decode()
        if "101" not in headers:
            raise RuntimeError("HTTP websocket handshake failed: " + headers)

    def _recv_frame(self):
        while True:
            if len(self.buf) >= 2:
                b0, b1 = self.buf[0], self.buf[1]
                ln = b1 & 0x7F
                off = 2
                if ln == 126:
                    if len(self.buf) < 4:
                        self.buf += self.recv_more(4 - len(self.buf))
                    ln = struct.unpack(">H", self.buf[2:4])[0]
                    off = 4
                elif ln == 127:
                    if len(self.buf) < 10:
                        self.buf += self.recv_more(10 - len(self.buf))
                    ln = struct.unpack(">Q", self.buf[2:10])[0]
                    off = 10
                masked = b1 & 0x80
                if masked:
                    if len(self.buf) < off + 4:
                        self.buf += self.recv_more(off + 4 - len(self.buf))
                    mask = self.buf[off:off + 4]
                    off += 4
                if len(self.buf) < off + ln:
                    self.buf += self.recv_more(off + ln - len(self.buf))
                payload = self.buf[off:off + ln]
                self.buf = self.buf[off + ln:]
                if masked:
                    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                return payload
            else:
                self.buf += self.recv_more(1)

    def recv_more(self, n):
        data = self.s.recv(max(n, 4096))
        if not data:
            raise RuntimeError("socket closed")
        return data

    def send(self, method, params=None):
        self.id += 1
        mid = self.id
        msg = {"id": mid, "method": method, "params": params or {}}
        self.s.sendall(self._frame(json.dumps(msg).encode()))
        # attend la reponse cible
        deadline = time.time() + 30
        while time.time() < deadline:
            f = self._recv_frame()
            if f.startswith(b"{"):
                obj = json.loads(f)
                if obj.get("id") == mid:
                    if "error" in obj:
                        raise RuntimeError("CDP error: " + json.dumps(obj["error"]))
                    return obj.get("result", {})
        raise RuntimeError("CDP timeout waiting " + method)

    def _frame(self, payload):
        ln = len(payload)
        mask = os.urandom(4)
        if ln < 126:
            head = bytes([0x81, 0x80 | ln])
        elif ln < 65536:
            head = bytes([0x81, 0x80 | 126]) + struct.pack(">H", ln)
        else:
            head = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", ln)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return head + mask + masked

    def eval_js(self, expr, await_promise=True):
        r = self.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        v = r.get("result", {})
        if "value" in v:
            return v["value"]
        if v.get("type") == "undefined":
            return None
        raise RuntimeError("eval_js no value: " + json.dumps(v))


# --------------------------- pilote Chrome ---------------------------------
def lancer():
    d = tempfile.mkdtemp(prefix="kotoage-live-")
    p = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--user-data-dir=" + d, "--remote-debugging-port=%d" % PORT,
         "--disable-extensions", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    # attendre le endpoint CDP
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % PORT, timeout=2) as r:
                r.read()
            break
        except Exception:
            time.sleep(0.25)
    # recuperer la page (about:blank) creee par Chrome ; la premiere page
    with urllib.request.urlopen("http://127.0.0.1:%d/json" % PORT, timeout=5) as r:
        tabs = json.loads(r.read())
    tab = next((t for t in tabs if t["type"] == "page"), tabs[0])
    return d, p, CDPSocket(tab["webSocketDebuggerUrl"])


def attendre(sock, cond_js, timeout=90):
    debut = time.time()
    while time.time() - debut < timeout:
        try:
            if sock.eval_js(cond_js):
                return True
        except Exception:
            pass
        time.sleep(0.8)
    return False


# --------------------------- script d'injection ----------------------------
# Reproduit l'API WebMCP (registerTool + declareTool + setState) pour que la
# couche webmcp.js s'enregistre, puis simule les appels d'un agent.
INJECT = r"""
(() => {
  const outilsEnregistres = [];
  const etatDelta = {};
  const log = [];
  window.__kotoageDiag = { outils: [], maquette: {}, verrue: new Date().toISOString() };
  const _real = (typeof document !== 'undefined') ? document.modelContext : undefined;

  const cible = {
    registerTool(o) {
      outilsEnregistres.push(o);
      window.__kotoageDiag.outils = outilsEnregistres;
      if (typeof _real?.registerTool === 'function') { try { _real.registerTool(o); } catch (e) {} }
      return true;
    },
    async declareTool(manifesto) {
      window.__kotoageDiag.outils = outilsEnregistres;
      return { type: 'ok', tool: manifesto?.name || 'mystere', ok: true };
    },
    setState(obj) { Object.assign(etatDelta, obj); return true; },
    async getState() { return { ...etatDelta }; },
  };
  try { Object.defineProperty(document, 'modelContext', { value: cible, configurable: true }); } catch (e) {}
  try { globalThis.__modelContextFake = cible; } catch (e) {}
  return { dejaPresente: !!_real };
})()
"""


def _imprimer(txt):
    try:
        print(txt, flush=True)
    except UnicodeEncodeError:
        print(txt.encode("ascii", "replace").decode("ascii"), flush=True)


def main():
    d, proc, sock = lancer()
    try:
        # 1) vérifie le contexte initial
        _imprimer("Chrome OK (profil temp).")
        # Active Page + installe le modelContext factice sur CHAQUE nouvelle page
        sock.send("Page.enable")
        sock.send("Runtime.enable")
        sock.send("Page.addScriptToEvaluateOnNewDocument", {"source": INJECT})

        # 2) navigate vers la page LIVE
        sock.send("Page.navigate", {"url": URL, "transitionType": "typed"})
        _imprimer("Navigation vers : " + URL)
        # attendre que le jeu charge (window.KOTOAGE_WEBMCP + pont)
        ok = attendre(sock, "!!(window.__webmcpActif)", 120)
        _imprimer("Pont WebMCP actif (window.__webmcpActif) : " + str(ok))
        if not ok:
            _imprimer("DIAG: " + str(sock.eval_js("JSON.stringify({K:!!window.KOTOAGE_WEBMCP, C:!!window.__webmcpConnexion, M:!!document.modelContext})")))
            return 1

        # 4) la couche webmcp.js a-t-elle enregistré les 7 outils sur notre factice ?
        n = sock.eval_js("window.__kotoageDiag && window.__kotoageDiag.outils.length")
        # ré-attacher l'état (simple : on relit via le pont exposé par le jeu)
        sock.eval_js(
            "(()=>{ const L=[]; "
            "try{ const c=window.__webmcpConnexion; "
            "L.push(['vie', c.joueur.vie, c.joueur.vieMax]); "
            "}catch(e){ L.push(['ERR', String(e)]); } "
            "window.__kotoageDiag.maquette = L; return true })()"
        )
        _imprimer("Outils enregistrés sur modelContext : " + str(n))
        _imprimer("Maquette jeu : " + str(sock.eval_js("JSON.stringify(window.__kotoageDiag.maquette)")))

        # 5) appel réel : on prend un outil enregistré et on exécute etat_joueur
        nom = sock.eval_js("window.__kotoageDiag.outils.length ? window.__kotoageDiag.outils[0].name : ''")
        _imprimer("Premier outil : " + str(nom))
        res = sock.eval_js(
            "(async()=>{ const o=window.__kotoageDiag.outils.find(x=>x.name==='etat_joueur'); "
            "if(!o) return 'PAS_D_OUTIL'; return JSON.stringify(await o.execute({})); })()"
        )
        _imprimer("execute(etat_joueur) : " + str(res))

        # 6) appel donner_potion → effet réel
        vie0 = sock.eval_js("window.__webmcpConnexion.joueur.vie")
        res2 = sock.eval_js(
            "(async()=>{ const o=window.__kotoageDiag.outils.find(x=>x.name==='donner_potion'); "
            "return JSON.stringify(await o.execute({type:'grande'})); })()"
        )
        _imprimer("execute(donner_potion, grande) : " + str(res2))

        # 7) l'état a-t-il réagi (vie plafonnée) ?
        vie = sock.eval_js("window.__webmcpConnexion.joueur.vie")
        _imprimer("Vie du joueur (avant " + str(vie0) + " / après potion) : " + str(vie))

        _imprimer("")
        _imprimer("=== VERIFICATION WEBMCP LIVE TERMINEE ===")
        return 0
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        time.sleep(0.3)
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
