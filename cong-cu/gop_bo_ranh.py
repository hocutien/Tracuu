"""Gộp kết quả thu bộ ranh của một tỉnh vào du-lieu/bo-ranh.json VÀ chép danh sách vào index.html (VNBOMD),
tăng số phiên bản (#appver trong index.html, PHIEN trong sw.js) để mỗi lần chỉ cần tải index.html + sw.js lên GitHub.

Cách dùng (chạy trong thư mục dự án):
    python cong-cu/gop_bo_ranh.py <file_thu.json> "<tên tỉnh>" [ghi chú]
    python cong-cu/gop_bo_ranh.py --chi-dong-bo          # chỉ chép bo-ranh.json hiện có vào index.html (+ tăng phiên bản)

<file_thu.json> là kết quả đoạn "tính phạm vi" trong docs/THU-BO-RANH.md (bước 4), dạng
    {"bo":[{"id":1998,"b":[vĩ nhỏ, kinh nhỏ, vĩ lớn, kinh lớn],"noi":["ĐT|TP Cao Lãnh", ...]}, ...],
     "so_diem": 12, "diem_rong": ["TG|TP Mỹ Tho", ...]}
"""
import json, sys, datetime, os, re

DICH = os.path.join('du-lieu', 'bo-ranh.json')


def ghi_json(cu):
    with open(DICH, 'w', encoding='utf-8', newline='\n') as f:
        f.write('{\n')
        f.write('  "mo_ta": ' + json.dumps(cu['mo_ta'], ensure_ascii=False) + ',\n')
        f.write('  "cap_nhat": "' + cu['cap_nhat'] + '",\n')
        f.write('  "da_thu": [\n' + ',\n'.join('    ' + json.dumps(d, ensure_ascii=False) for d in cu['da_thu']) + '\n  ],\n')
        f.write('  "bo": [\n' + ',\n'.join('    ' + json.dumps(b, ensure_ascii=False) for b in cu['bo']) + '\n  ]\n}\n')


def kho_ranh():
    """Tóm tắt bo-ranh.json theo tỉnh đã thu: t = tên, d = số huyện có ranh, b = số bộ, n = ngày mới nhất, h = tên huyện (nếu ghi), r = huyện chưa có ranh.
    Các mục da_thu cùng tỉnh ("Đồng Tháp mới — phần …") gộp thành một dòng."""
    cu = json.load(open(DICH, encoding='utf-8'))
    khoa = lambda t: t.split(' — ')[0].split(' (')[0].strip()
    out = {}
    for d in cu['da_thu']:
        k = khoa(d['tinh'])
        gc = d.get('ghi_chu', '')
        r = [x.split('|', 1)[-1].strip() for x in gc.split('điểm không có ranh: ', 1)[1].split(';')[0].split(',')] if 'điểm không có ranh: ' in gc else []
        m = re.match(r'(\d+)/\d+ điểm không có ranh', gc)
        rong = len(r) if r else (int(m.group(1)) if m else 0)
        o = out.setdefault(k, {'t': d['tinh'] if ' — ' not in d['tinh'] else k, 'd': 0, 'b': 0, 'n': '', 'h': [], 'r': [], 'k': []})
        o['d'] += max(0, d.get('so_diem', 0) - rong - len(d.get('o_rong', [])))
        o['k'] += d.get('o_rong', [])   # trang nguồn có tải ô nhưng ô tại trung tâm huyện rỗng
        o['n'] = max(o['n'], d.get('ngay', ''))
        o['r'] += r
        if m:
            o['r'].append('%d huyện ở %s' % (rong, d['tinh'].split(' — ')[-1]))
    for k, o in out.items():
        bo = [b for b in cu['bo'] if any(khoa(n.split(': ')[0]) == k for n in b.get('noi', []))]
        o['b'] = len(bo)
        o['h'] = sorted({n.split(': ', 1)[1] for b in bo for n in b.get('noi', []) if ': ' in n and khoa(n.split(': ')[0]) == k} - set(o['k']))
    return list(out.values())


def dong_bo_index(bo):
    """Viết lại khối const VNBOMD=[…] trong index.html và tăng phiên bản (index.html + sw.js)."""
    s = open('index.html', encoding='utf-8').read()
    i = s.index('const VNBOMD=[')
    j = s.index('];', i) + 2
    k = s.index('\n', j)
    dong = ',\n  '.join(','.join('{id:%d,b:[%s]}' % (b['id'], ','.join('%g' % v for v in b['b'])) for b in bo[n:n + 6])
                        for n in range(0, len(bo), 6))
    s = s[:i] + 'const VNBOMD=[\n  ' + dong + '];   // chép từ du-lieu/bo-ranh.json (' + str(len(bo)) + ' bộ) bằng cong-cu/gop_bo_ranh.py' + s[k:]
    # v59: bảng «Kho ranh» (tỉnh, số huyện đã thu, số bộ, ngày, tên huyện) cho giao diện
    kho = 'const VNKHO=' + json.dumps(kho_ranh(), ensure_ascii=False, separators=(',', ':')) + ';   // chép từ du-lieu/bo-ranh.json bằng cong-cu/gop_bo_ranh.py'
    if '\nconst VNKHO=' in s:
        s = re.sub(r'\nconst VNKHO=[^\n]*', lambda _: '\n' + kho, s, count=1)
    else:
        k2 = s.index('\n', s.index('const VNBOMD=['))
        k2 = s.index('\n', s.index('];', k2))
        s = s[:k2] + '\n' + kho + s[k2:]
    m = re.search(r'(id="appver"[^>]*>)v(\d+) · [0-9/]+<', s)
    so = int(m.group(2)) + 1
    hom = datetime.date.today().strftime('%d/%m/%Y')
    s = s[:m.start()] + m.group(1) + 'v%d · %s<' % (so, hom) + s[m.end():]
    open('index.html', 'w', encoding='utf-8', newline='').write(s)
    w = open('sw.js', encoding='utf-8').read()
    w = re.sub(r"tcdt-v\d+", 'tcdt-v%d' % so, w, count=1)
    open('sw.js', 'w', encoding='utf-8', newline='').write(w)
    return so


if len(sys.argv) >= 2 and sys.argv[1] == '--chi-dong-bo':
    cu = json.load(open(DICH, encoding='utf-8'))
    so = dong_bo_index(cu['bo'])
    print(f'Đã chép {len(cu["bo"])} bộ vào index.html, phiên bản v{so}. Tải index.html + sw.js lên GitHub.')
    sys.exit(0)
if len(sys.argv) < 3:
    sys.exit(__doc__)
nguon, tinh = sys.argv[1], sys.argv[2]
ghi = sys.argv[3] if len(sys.argv) > 3 else ''
cu = json.load(open(DICH, encoding='utf-8'))
moi = json.load(open(nguon, encoding='utf-8'))
bo = {b['id']: b for b in cu['bo']}
them = nori = 0
for x in moi['bo']:
    noi = [tinh + ': ' + n.split('|', 1)[-1] for n in x.get('noi', [])]
    if x['id'] in bo:
        b, c = bo[x['id']]['b'], x['b']
        bo[x['id']]['b'] = [min(b[0], c[0]), min(b[1], c[1]), max(b[2], c[2]), max(b[3], c[3])]
        bo[x['id']]['noi'] = list(dict.fromkeys(bo[x['id']]['noi'] + noi))
        nori += 1
    else:
        bo[x['id']] = {'id': x['id'], 'b': x['b'], 'noi': noi}
        them += 1
hom = datetime.date.today().isoformat()
muc = {'tinh': tinh, 'ngay': hom, 'so_diem': moi.get('so_diem', 0)}
if moi.get('diem_rong'):
    muc['ghi_chu'] = 'điểm không có ranh: ' + ', '.join(moi['diem_rong'])
if ghi:
    muc['ghi_chu'] = (muc.get('ghi_chu', '') + '; ' + ghi).strip('; ')
cu['da_thu'].append(muc)
cu['cap_nhat'] = hom
cu['bo'] = sorted(bo.values(), key=lambda b: b['id'])
ghi_json(cu)
so = dong_bo_index(cu['bo'])
print(f'Thêm {them} bộ mới, nới {nori} bộ đã có; tổng {len(cu["bo"])} bộ. Đã chép vào index.html, phiên bản v{so}.')
print('Tải lên GitHub: index.html, sw.js (và du-lieu/bo-ranh.json nếu muốn giữ bản gốc trên trang).')
