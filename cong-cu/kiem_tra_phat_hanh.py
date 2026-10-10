"""So bản trên máy với bản đang chạy trên GitHub Pages, in ra file nào chưa tải / còn cũ.

Cách dùng (trong thư mục dự án):  python cong-cu/kiem_tra_phat_hanh.py
Chỉ ĐỌC trang GitHub (không đăng nhập, không đẩy file).
"""
import hashlib, os, re, sys, time, urllib.request, urllib.error

GOC = 'https://hocutien.github.io/Tracuu/'
TEP = ['index.html', 'sw.js', 'manifest.webmanifest', 'du-lieu/bo-ranh.json', 'cong-cu/bo-sung-tu-dong.user.js',
       'icon-192.png', 'icon-512.png', 'icon-maskable-512.png']


def tai(duong):
    try:
        r = urllib.request.urlopen(urllib.request.Request(GOC + duong + '?kt=%d' % time.time(), headers={'User-Agent': 'kiem-tra-phat-hanh', 'Cache-Control': 'no-cache'}), timeout=30)
        return r.read()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)


def phien(b):
    m = re.search(rb'id="appver"[^>]*>([^<]+)<', b or b'')
    return m.group(1).decode('utf-8') if m else '?'


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
can = []
for t in TEP:
    if not os.path.exists(t):
        continue
    may = open(t, 'rb').read()
    web = tai(t)
    if web == 404:
        trang = 'CHƯA CÓ trên GitHub'
        can.append(t)
    elif isinstance(web, (int, str)):
        trang = 'không đọc được (%s)' % web
    elif hashlib.sha1(may.replace(b'\r\n', b'\n')).digest() == hashlib.sha1(web.replace(b'\r\n', b'\n')).digest():
        trang = 'khớp'
    else:
        trang = 'KHÁC bản trên máy'
        can.append(t)
    them = ''
    if t == 'index.html' and isinstance(web, bytes):
        them = f'  (máy: {phien(may)} · GitHub: {phien(web)})'
    print(f'{t:28} {trang}{them}')
print()
if can:
    print('Cần tải lên GitHub:', ', '.join(can))
    print('(GitHub Pages có thể chậm 1–2 phút sau khi tải; chạy lại để kiểm tra.)')
else:
    print('GitHub đã khớp bản trên máy.')
