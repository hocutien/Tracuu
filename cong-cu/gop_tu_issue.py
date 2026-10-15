"""Gộp bộ ranh do app / tiện ích gửi lên kho (một issue GitHub) vào du-lieu/bo-ranh.json, chép vào index.html, tăng phiên bản.
GitHub Actions (.github/workflows/gop-bo-ranh.yml) chạy file này khi có issue mới; chạy tay cũng được:
    python cong-cu/gop_tu_issue.py <file chứa nội dung issue>      (không có tham số thì đọc biến môi trường NOI_DUNG)

Nội dung issue (do nút «📤 Gửi lên kho» tạo, xem vnGuiKho trong index.html và cong-cu/thu-bo-ranh.user.js):
    <!-- bo-ranh v1 -->
    ```
    moi 3173:9.61700,106.15000,9.78500,106.36400;3174:…      bộ mới / phạm vi nới rộng (vĩ nhỏ, kinh nhỏ, vĩ lớn, kinh lớn)
    xoa 2826                                               bộ trang nguồn đã xoá (ô trả 404 «Dataset not found»)
    uu_tien Trà Vinh|An Giang|…                            thứ tự tỉnh ưu tiên rà
    ```
Tệp này KHÔNG gọi onland.vn: chỉ gộp những gì người dùng thật đã thấy khi xem bản đồ (robots.txt của onland.vn cấm máy tự động vào /api/).
Kết quả in ra dòng cuối dạng «KQ: …» để workflow ghi vào bình luận; mã thoát 0 = có thay đổi, 3 = không có gì mới, 2 = nội dung sai.
"""
import json, os, re, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gop_bo_ranh as G

TRAN_BO = 300        # một lần gửi tối đa 300 bộ
TRAN_XOA = 5         # một lần gửi tối đa 5 bộ chết (nhiều hơn thì làm tay: có thể trạm hỏng chứ không phải nguồn xoá)
CANH_MAX = 2.0       # phạm vi một bộ không quá 2° mỗi chiều (một bộ ≈ một huyện)


def doc(nd):
    if '<!-- bo-ranh v1 -->' not in nd:
        raise ValueError('không có dấu «<!-- bo-ranh v1 -->»')
    moi, xoa, uu = {}, [], None
    for dong in nd.splitlines():
        dong = dong.strip()
        if dong.startswith('moi '):
            for p in dong[4:].split(';'):
                m = re.fullmatch(r'\s*(\d{1,6}):([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)\s*', p)
                if not m:
                    continue
                i, b = int(m.group(1)), [float(m.group(k)) for k in range(2, 6)]
                if not (5 < b[0] <= b[2] < 25 and 100 < b[1] <= b[3] < 112):
                    raise ValueError(f'bộ {i}: phạm vi ngoài Việt Nam {b}')
                if b[2] - b[0] > CANH_MAX or b[3] - b[1] > CANH_MAX:
                    raise ValueError(f'bộ {i}: phạm vi quá rộng {b}')
                c = moi.get(i)
                moi[i] = [min(c[0], b[0]), min(c[1], b[1]), max(c[2], b[2]), max(c[3], b[3])] if c else b
        elif dong.startswith('xoa '):
            xoa += [int(x) for x in re.findall(r'\d{1,6}', dong[4:])]
        elif dong.startswith('uu_tien '):
            uu = [t.strip()[:40] for t in dong[8:].split('|') if t.strip()][:70]
    if len(moi) > TRAN_BO:
        raise ValueError(f'{len(moi)} bộ, quá {TRAN_BO}')
    xoa = sorted(set(xoa))
    if len(xoa) > TRAN_XOA:
        raise ValueError(f'{len(xoa)} bộ chết một lần (quá {TRAN_XOA}): kiểm tra trạm trước, rồi gộp tay')
    return moi, xoa, uu


def gop(moi, xoa, uu, nhan):
    cu = json.load(open(G.DICH, encoding='utf-8'))
    bo = {b['id']: b for b in cu['bo']}
    dabo = set(cu.get('bo_xoa', []))
    them, nori, bo_di = [], [], []
    for i, b in moi.items():
        if i in dabo or i in xoa:
            continue
        if i in bo:
            c = bo[i]['b']
            n = [round(min(c[0], b[0]), 3), round(min(c[1], b[1]), 3), round(max(c[2], b[2]), 3), round(max(c[3], b[3]), 3)]
            if n != c:
                bo[i]['b'] = n
                nori.append(i)
        else:
            bo[i] = {'id': i, 'b': [round(v, 3) for v in b], 'noi': [nhan]}
            them.append(i)
    for i in xoa:
        if i in bo:
            del bo[i]
            bo_di.append(i)
        dabo.add(i)
    doi_uu = uu is not None and uu != cu.get('uu_tien')
    if not (them or nori or bo_di or doi_uu or dabo != set(cu.get('bo_xoa', []))):
        return None
    cu['bo'] = sorted(bo.values(), key=lambda b: b['id'])
    cu['bo_xoa'] = sorted(dabo)
    if uu is not None:
        cu['uu_tien'] = uu
    cu['cap_nhat'] = datetime.date.today().isoformat()
    G.ghi_json(cu)
    so = G.dong_bo_index(cu['bo'], cu['bo_xoa'])
    return dict(them=them, nori=nori, bo_di=bo_di, doi_uu=doi_uu, so=so, tong=len(cu['bo']))


def main():
    nd = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv) > 1 else os.environ.get('NOI_DUNG', '')
    nhan = 'Gửi lên kho ' + (('#' + os.environ['SO_ISSUE'] + ' ') if os.environ.get('SO_ISSUE') else '') + datetime.date.today().isoformat()
    try:
        moi, xoa, uu = doc(nd)
    except ValueError as e:
        print('KQ: Không gộp — nội dung sai: ' + str(e))
        sys.exit(2)
    kq = gop(moi, xoa, uu, nhan)
    if not kq:
        print('KQ: Không có gì mới (các bộ gửi lên đã có sẵn trong kho, phạm vi không rộng hơn).')
        sys.exit(3)
    phan = []
    if kq['them']:
        phan.append(f"thêm {len(kq['them'])} bộ mới ({', '.join(map(str, kq['them'][:20]))}{'…' if len(kq['them']) > 20 else ''})")
    if kq['nori']:
        phan.append(f"nới phạm vi {len(kq['nori'])} bộ")
    if kq['bo_di']:
        phan.append(f"bỏ {len(kq['bo_di'])} bộ nguồn đã xoá ({', '.join(map(str, kq['bo_di']))})")
    if kq['doi_uu']:
        phan.append('cập nhật thứ tự tỉnh ưu tiên')
    print(f"KQ: Đã {'; '.join(phan)}. Tổng {kq['tong']} bộ, phiên bản v{kq['so']}.")
    with open(os.environ.get('GITHUB_OUTPUT', os.devnull), 'a', encoding='utf-8') as f:
        f.write(f"phien=v{kq['so']}\n")


if __name__ == '__main__':
    main()
