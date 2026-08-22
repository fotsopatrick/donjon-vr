#!/usr/bin/env python3
"""Analyseur de captures PNG (pur Python, sans dépendance).

Décode un PNG 8-bit RGB/RGBA non entrelacé et calcule des métriques
objectives : luminosité moyenne, saturation, fraction surexposée,
et métriques par bandes (haut = ciel/fond, milieu = maisons, bas = sol).

Usage : python3 analyser-capture.py <fichier.png> [--bandes]
"""
import sys
import zlib
import struct


def decodage_png(chemin):
    with open(chemin, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'pas un PNG'
    pos = 8
    w = h = None
    bit, ctype, entrelace = None, None, None
    idat = b''
    while pos < len(data):
        ln, typ = struct.unpack('>I4s', data[pos:pos + 8])
        corps = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bit, ctype, _, _, entrelace = struct.unpack('>IIBBBBB', corps)
        elif typ == b'IDAT':
            idat += corps
        elif typ == b'IEND':
            break
    assert bit == 8, 'bit depth %d non supporte' % bit
    assert entrelace == 0, 'entrelace non supporte'
    if ctype == 2:
        canaux = 3
    elif ctype == 6:
        canaux = 4
    else:
        raise SystemExit('color type %d non supporte' % ctype)
    brut = zlib.decompress(idat)
    lignes = []
    pos = 0
    for _ in range(h):
        filt = brut[pos]
        pos += 1
        ligne = bytearray(brut[pos:pos + w * canaux])
        pos += w * canaux
        if filt == 1:
            for i in range(canaux, len(ligne)):
                ligne[i] = (ligne[i] + ligne[i - canaux]) & 255
        elif filt == 2:
            prev = lignes[-1] if lignes else None
            for i in range(len(ligne)):
                ligne[i] = (ligne[i] + (prev[i] if prev else 0)) & 255
        elif filt == 3:
            prev = lignes[-1] if lignes else None
            for i in range(len(ligne)):
                a = ligne[i - canaux] if i >= canaux else 0
                b = prev[i] if prev else 0
                ligne[i] = (ligne[i] + ((a + b) // 2)) & 255
        elif filt == 4:
            prev = lignes[-1] if lignes else None
            for i in range(len(ligne)):
                a = ligne[i - canaux] if i >= canaux else 0
                b = prev[i] if prev else 0
                c = prev[i - canaux] if (prev and i >= canaux) else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                ligne[i] = (ligne[i] + pred) & 255
        elif filt != 0:
            raise SystemExit('filtre %d inconnu' % filt)
        lignes.append(bytes(ligne))
    return w, h, canaux, lignes


def metrique(w, h, canaux, lignes, x0=0, y0=0, x1=None, y1=None):
    x1 = x1 or w
    y1 = y1 or h
    n = 0
    sr = sg = sb = 0
    sat_tot = 0.0
    sur_exp = 0
    for y in range(y0, y1):
        ligne = lignes[y]
        for x in range(x0, x1):
            i = (x * canaux)
            r, g, b = ligne[i], ligne[i + 1], ligne[i + 2]
            n += 1
            sr += r; sg += g; sb += b
            mx, mn = max(r, g, b), min(r, g, b)
            sat_tot += (mx - mn) / 255.0
            if (r + g + b) / 3.0 > 235:
                sur_exp += 1
    if not n:
        return None
    mr, mg, mb = sr / n, sg / n, sb / n
    lum = 0.2126 * mr + 0.7152 * mg + 0.0722 * mb
    return {'pixels': n, 'moy': (round(mr), round(mg), round(mb)),
            'luminosite': round(lum, 1), 'saturation': round(sat_tot / n, 3),
            'surexposes_pct': round(100.0 * sur_exp / n, 1)}


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage : analyser-capture.py <fichier.png>')
    chemin = sys.argv[1]
    w, h, canaux, lignes = decodage_png(chemin)
    print('taille : %dx%d, canaux=%d' % (w, h, canaux))
    g = metrique(w, h, canaux, lignes)
    print('GLOBAL : %s' % g)
    if '--bandes' in sys.argv:
        labels = [('ciel/fond  ', 0, int(h * 0.22)),
                  ('horizon    ', int(h * 0.22), int(h * 0.42)),
                  ('maisons    ', int(h * 0.42), int(h * 0.62)),
                  ('sol/place  ', int(h * 0.62), int(h * 0.85)),
                  ('bas        ', int(h * 0.85), h)]
        for nom, y0, y1 in labels:
            m = metrique(w, h, canaux, lignes, 0, y0, w, y1)
            if m:
                print('  %s : %s' % (nom, m))


if __name__ == '__main__':
    main()
