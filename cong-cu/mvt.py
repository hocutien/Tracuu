import urllib.request, math, json, sys

def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1
        r |= (c & 0x7f) << s; s += 7
        if c < 0x80: return r, i

def fields(b):
    i = 0
    while i < len(b):
        k, i = varint(b, i); f, t = k >> 3, k & 7
        if t == 0: v, i = varint(b, i)
        elif t == 2:
            n, i = varint(b, i); v = b[i:i+n]; i += n
        elif t == 5: v = b[i:i+4]; i += 4
        elif t == 1: v = b[i:i+8]; i += 8
        else: raise ValueError(t)
        yield f, t, v

def packed(b):
    i = 0; out = []
    while i < len(b):
        v, i = varint(b, i); out.append(v)
    return out

def zz(n): return (n >> 1) ^ -(n & 1)

def value(b):
    import struct
    for f, t, v in fields(b):
        if f == 1: return v.decode()
        if f == 2: return struct.unpack('<f', v)[0]
        if f == 3: return struct.unpack('<d', v)[0]
        if f in (4, 5): return v
        if f == 6: return zz(v)
        if f == 7: return bool(v)

def geom(cmds):
    rings = []; x = y = 0; i = 0; cur = None
    while i < len(cmds):
        c = cmds[i]; i += 1; op, n = c & 7, c >> 3
        if op == 7:
            if cur: rings.append(cur); cur = None
            continue
        for _ in range(n):
            x += zz(cmds[i]); y += zz(cmds[i+1]); i += 2
            if op == 1:
                if cur: rings.append(cur)
                cur = [(x, y)]
            else: cur.append((x, y))
    if cur: rings.append(cur)
    return rings

def decode(b):
    out = []
    for f, t, v in fields(b):
        if f != 3: continue
        keys = []; vals = []; feats = []; ext = 4096; name = ''
        for f2, t2, v2 in fields(v):
            if f2 == 1: name = v2.decode()
            elif f2 == 3: keys.append(v2.decode())
            elif f2 == 4: vals.append(value(v2))
            elif f2 == 5: ext = v2
            elif f2 == 2: feats.append(v2)
        for fb in feats:
            tags = []; g = []; typ = 0; fid = None
            for f3, t3, v3 in fields(fb):
                if f3 == 1: fid = v3
                elif f3 == 2: tags = packed(v3)
                elif f3 == 3: typ = v3
                elif f3 == 4: g = packed(v3)
            props = {keys[tags[k]]: vals[tags[k+1]] for k in range(0, len(tags), 2)}
            out.append(dict(layer=name, ext=ext, type=typ, props=props, rings=geom(g)))
    return out

def tile(ds, z, x, y):
    u = f"https://onland.vn/api/diachinh/api/cadastral/datasets/{ds}/tiles/{z}/{x}/{y}.mvt"
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()

def xy(lat, lng, z):
    n = 2 ** z
    return (lng + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n

def ll(z, tx, ty, px, py, ext):
    n = 2 ** z; X = tx + px / ext; Y = ty + py / ext
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y / n)))), X / n * 360 - 180
