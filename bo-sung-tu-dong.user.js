// ==UserScript==
// @name         Tra cứu thửa đất – bổ sung thông tin tự động
// @namespace    https://hocutien.github.io/Tracuu/
// @version      1.0
// @description  Khi app Tra cứu thửa đất mở trang soi quy hoạch kèm mã #tcdt=…, tự lấy số tờ, số thửa, loại đất, diện tích của các thửa đang chọn bằng chính phiên trình duyệt của bạn rồi gửi về app và đóng thẻ. Không lấy tên chủ sử dụng đất.
// @match        https://guland.vn/soi-quy-hoach*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

/* Cách hoạt động (giống nút dấu trang «📥 Bổ sung thửa» của app, chỉ khác là tự chạy):
   - Chỉ chạy khi địa chỉ có #tcdt=… do app tạo; mở trang bình thường thì không làm gì.
   - Chỉ gửi kết quả cho app ở các địa chỉ trong GOC_OK (trang của tác giả, máy thử cục bộ) — trang lạ mở kèm #tcdt= sẽ bị bỏ qua.
   - Hỏi từng thửa bằng jQuery của chính trang (như khi bạn tự bấm vào bản đồ), tối đa 10 thửa, cách nhau 0,8 giây.
   - Trang đòi kiểm tra chống máy tự động thì bạn tự bấm qua; tiện ích không làm thay. */
(async () => {
  const GOC_OK = /^(https:\/\/hocutien\.github\.io|http:\/\/(localhost|127\.0\.0\.1)(:\d+)?)$/;
  const h = location.hash.match(/tcdt=([^&]+)/);
  if (!h) return;
  let q;
  try { q = JSON.parse(decodeURIComponent(h[1])); } catch (e) { return; }
  if (!q || !Array.isArray(q.d) || !GOC_OK.test(String(q.o || ''))) return;
  let goc = '';
  try { goc = new URL(q.a).origin; } catch (e) {}
  if (goc !== q.o) return;                       // địa chỉ quay về phải cùng gốc với app đã mở thẻ này

  const B = document.createElement('div');
  B.style.cssText = 'position:fixed;z-index:2147483647;top:70px;left:50%;transform:translateX(-50%);background:#12283a;color:#fbeed0;font:14px/1.4 Arial,sans-serif;padding:10px 14px;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.4);max-width:92vw';
  B.textContent = 'Tra cứu thửa đất: đang chờ trang tải xong…';
  document.body.appendChild(B);

  for (let i = 0; i < 60 && !window.jQuery; i++) await new Promise(r => setTimeout(r, 250));
  if (!window.jQuery) { B.textContent = 'Tra cứu thửa đất: trang chưa tải xong, hãy tải lại thẻ này.'; return; }
  await new Promise(r => setTimeout(r, 1500));   // chờ trang tự cài mã phiên cho các lời gọi của nó

  const kq = [];
  for (let i = 0; i < q.d.length && i < 10; i++) {
    const p = q.d[i];
    B.textContent = 'Tra cứu thửa đất: đang lấy thửa ' + (i + 1) + '/' + Math.min(q.d.length, 10) + '…';
    let j = null;
    try {
      j = await new Promise((ok, er) => window.jQuery.ajax({
        url: '/get-bound-2', method: 'POST', dataType: 'json',
        data: { marker_lat: p.la, marker_lng: p.lo, area: '', shape: '', force_remap_id: '', force_hcm_bddc_id: '', province_id: p.t || '' },
        success: ok, error: (x, s) => er(new Error(s + ' ' + x.status))
      }));
    } catch (e) { kq.push({ k: p.k, loi: String(e.message) }); continue; }
    const d = document.createElement('div');
    d.innerHTML = String(j && j.html || '');
    const txt = d.textContent.replace(/\s+/g, ' ').replace(/Tên chủ.*?(?=Dữ liệu|$)/, ' ');   // bỏ tên chủ ngay tại đây
    const ma = (txt.match(/\b([0-9]?[A-Z]{2,4}(?:[+-][A-Z]{2,4})*)\s+[0-9.,]+\s*m²\s*([^0-9]*?)(?=Dữ liệu|Xem đầy đủ|$)/) || []);
    const A = [...d.querySelectorAll('a')].map(x => x.textContent.trim());
    const ix = A.findIndex(x => /^(Xã|Phường|Thị trấn)\s/.test(x));
    const ok3 = x => x && x.length < 40 && !/[0-9]/.test(x) && !/Chỉ đường|Đo vẽ|Bảng|Ký hiệu|Xem/.test(x);
    const dc = ix < 0 ? [] : ['', A[ix], ok3(A[ix + 1]) ? A[ix + 1] : '', ok3(A[ix + 2]) ? A[ix + 2] : ''];
    kq.push({ k: p.k, j: { status: j && j.status, points: j && j.points, address: j && j.address, district_id: j && j.district_id, ward_id: j && j.ward_id,
      ma: ma[0] || '', loai: (ma[2] || '').trim(), xa: dc[1] || '', huyen: dc[2] || '', tinh: dc[3] || '' } });
    if (i + 1 < q.d.length) await new Promise(r => setTimeout(r, 800));
  }
  const n = kq.filter(x => x.j && x.j.points).length;
  if (window.opener && !window.opener.closed) {
    window.opener.postMessage({ tcdt: 'gl', kq }, q.o);
    B.textContent = 'Tra cứu thửa đất: đã gửi ' + n + '/' + kq.length + ' thửa có số liệu về app. Thẻ này tự đóng…';
    setTimeout(() => window.close(), 1200);
  } else {
    B.textContent = 'Tra cứu thửa đất: đã lấy ' + n + '/' + kq.length + ' thửa — đang mở lại app…';
    location.href = q.a + '#glkq=' + encodeURIComponent(JSON.stringify(kq));
  }
})();
