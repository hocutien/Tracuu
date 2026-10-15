// ==UserScript==
// @name         Tra cứu thửa đất – tự thu bộ ranh khi xem bản đồ
// @namespace    https://hocutien.github.io/Tracuu/
// @version      1.0
// @description  Khi bạn tự xem bản đồ quy hoạch trên onland.vn, ghi lại số bộ ranh mà chính trang đó tải (giống nút dấu trang «📥 Lấy bộ ranh»), so với kho của app và cho gửi phần mới lên kho (GitHub tự gộp) hoặc mở thẳng trong app. Không tự mở trang, không tự gọi gì thêm.
// @match        https://onland.vn/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

/* Cách hoạt động:
   - Móc Worker.prototype.postMessage của trang để đọc địa chỉ ô ranh «datasets/<bộ>/tiles/<z>/<x>/<y>» mà trang tự tải khi bạn kéo / phóng bản đồ
     (cùng cách với nút dấu trang của app, docs/THU-BO-RANH.md). Không gọi thêm lời nào tới onland.vn.
   - Lấy danh sách bộ đã có của app (du-lieu/bo-ranh.json trên GitHub Pages, nhớ 12 giờ) → chỉ giữ bộ MỚI hoặc phạm vi RỘNG HƠN.
   - Phần mới cộng dồn qua các lần xem (localStorage của trang này) tới khi bạn bấm Gửi.
   - «📤 Gửi lên kho»: mở trang tạo issue GitHub đã điền sẵn; bạn bấm «Submit new issue» → GitHub Actions gộp vào app (cong-cu/gop_tu_issue.py).
     Issue là công khai: chỉ chứa số bộ và khung toạ độ ô (≈ 0,6 km), không có gì khác.
   - «Mở trong app»: mở app kèm #vnbo=… (chỉ lưu trong trình duyệt đó, như nút dấu trang). */
(() => {
  const APP = 'https://hocutien.github.io/Tracuu/';
  const KHO = 'https://github.com/hocutien/Tracuu/issues/new';
  const KHOA = '__tcdt_thu', KHOADS = '__tcdt_ds', LE = 0.002, TOIDA = 150;
  const doc = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) || d } catch (e) { return d } };
  const ghi = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch (e) {} };
  const ll = (z, x, y) => { const n = 2 ** z; return [Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n))) * 180 / Math.PI, x / n * 360 - 180] };

  let S = doc(KHOA, {});                       // bộ → [vĩ nhỏ, kinh nhỏ, vĩ lớn, kinh lớn] đã thấy, chưa gửi
  let DS = null;                               // bộ đã có trong kho: id → khung
  const dsCu = doc(KHOADS, null);
  if (dsCu && Date.now() - dsCu.t < 12 * 3600e3) DS = dsCu.d;
  else fetch(APP + 'du-lieu/bo-ranh.json', { cache: 'no-cache' }).then(r => r.json()).then(j => {
    DS = {}; for (const b of j.bo || []) DS[b.id] = b.b;
    for (const id of j.bo_xoa || []) DS[id] = 'xoa';
    ghi(KHOADS, { t: Date.now(), d: DS }); ve();
  }).catch(() => {});

  const moi = () => {                          // phần mới so với kho
    const out = {};
    for (const [id, b] of Object.entries(S)) {
      const k = DS && DS[id];
      if (k === 'xoa') continue;
      if (!k || b[0] < k[0] - LE || b[1] < k[1] - LE || b[2] > k[2] + LE || b[3] > k[3] + LE) out[id] = b;
    }
    return out;
  };
  const ma = o => Object.entries(o).slice(0, TOIDA).map(([id, b]) => id + ':' + b.map(v => v.toFixed(5)).join(',')).join(';');

  const op = Worker.prototype.postMessage;
  Worker.prototype.postMessage = function (m, ...r) {
    try {
      const s = JSON.stringify(m, (k, v) => v instanceof ArrayBuffer || ArrayBuffer.isView(v) ? undefined : v);
      const re = /datasets\/(\d+)\/tiles\/(\d+)\/(\d+)\/(\d+)/g; let q, doi = false;
      while ((q = re.exec(s))) {
        const [, id, z, x, y] = q.map(Number);
        const a = ll(z, x, y + 1), c = ll(z, x + 1, y), b = S[id];
        const n = b ? [Math.min(b[0], a[0]), Math.min(b[1], a[1]), Math.max(b[2], c[0]), Math.max(b[3], c[1])] : [a[0], a[1], c[0], c[1]];
        if (!b || n.some((v, i) => v !== b[i])) { S[id] = n; doi = true }
      }
      if (doi) { ghi(KHOA, S); hen() }
    } catch (e) {}
    return op.call(this, m, ...r);
  };

  let H = null, an = false, hoan = 0;
  const hen = () => { clearTimeout(hoan); hoan = setTimeout(ve, 600) };
  function ve() {
    if (!document.body || an) return;
    const o = moi(), n = Object.keys(o).length;
    if (!n) { if (H) H.remove(); H = null; return }
    if (!H) {
      H = document.createElement('div');
      H.style.cssText = 'position:fixed;z-index:2147483647;left:12px;bottom:12px;background:#12283a;color:#fbeed0;font:14px/1.4 Arial,sans-serif;padding:10px 12px;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.4);max-width:min(340px,92vw)';
      document.body.appendChild(H);
    }
    const moiHan = Object.keys(o).filter(id => !(DS && DS[id])).length;
    H.innerHTML = `<b>🧩 Tra cứu thửa đất</b><br>Đã thấy ${moiHan ? moiHan + ' bộ ranh mới' : ''}${moiHan && n > moiHan ? ', ' : ''}${n > moiHan ? (n - moiHan) + ' bộ rộng hơn kho' : ''}${DS ? '' : ' (chưa so được với kho)'}.<br>`;
    const nut = (t, nen, fn) => { const b = document.createElement('button'); b.textContent = t; b.style.cssText = `margin:6px 6px 0 0;min-height:36px;padding:6px 12px;border:0;border-radius:6px;background:${nen};color:#fff;font-weight:700;cursor:pointer`; b.onclick = fn; H.appendChild(b) };
    nut('📤 Gửi lên kho', '#3d6b4f', () => {
      const o2 = moi(), s = ma(o2), dem = Math.min(Object.keys(o2).length, TOIDA);
      const body = `<!-- bo-ranh v1 -->\nGửi từ tiện ích thu bộ ranh ngày ${new Date().toLocaleDateString('vi-VN')}: ${dem} bộ. Bấm «Submit new issue» (Tạo) để gửi; GitHub tự gộp vào app sau 1–2 phút.\n\n\`\`\`\nmoi ${s}\n\`\`\`\n`;
      window.open(KHO + '?title=' + encodeURIComponent(`Bộ ranh: ${dem} bộ (tiện ích)`) + '&body=' + encodeURIComponent(body), '_blank');
      for (const id of Object.keys(o2).slice(0, TOIDA)) delete S[id];
      ghi(KHOA, S);
      if (DS) { for (const [id, b] of Object.entries(o2)) { const k = DS[id]; DS[id] = k && k !== 'xoa' ? [Math.min(k[0], b[0]), Math.min(k[1], b[1]), Math.max(k[2], b[2]), Math.max(k[3], b[3])] : b } ghi(KHOADS, { t: dsCu && dsCu.t || Date.now(), d: DS }) }
      ve();
    });
    nut('Mở trong app', '#1d5fd0', () => window.open(APP + '#vnbo=' + ma(moi()), '_blank'));
    nut('Ẩn', '#6d6a60', () => { an = true; H.remove(); H = null });
  }
  document.addEventListener('DOMContentLoaded', ve);
})();
