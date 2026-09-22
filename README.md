# Tra cứu thửa đất — bản cài được lên màn hình chính

Công cụ đọc bản đồ địa chính `.dgn` / `.dxf`, tìm thửa và xuất KMZ xem trên Google Earth.
Mọi thứ chạy trong máy: file bản đồ không được gửi đi đâu cả.

## Vì sao phải đưa lên một địa chỉ web

Mở file HTML thẳng từ trình quản lý file trên Android, Chrome chỉ cấp cho trang một
địa chỉ tạm dùng một lần (`content://…`). Tải lại trang là mất quyền đọc, và trình
duyệt cũng không cho dùng định vị GPS. Đặt lên một địa chỉ `https` thì hết cả hai:
mở một chạm từ màn hình chính, tải lại thoải mái, GPS xin phép bình thường.

## Các bước làm một lần

1. Đăng nhập <https://github.com>, bấm **New repository**.
   - Tên: `tracuu` (hoặc tên gì cũng được)
   - Chọn **Public** — tài khoản miễn phí chỉ mở web được cho repo công khai
   - Bấm **Create repository**
2. Ở màn hình vừa hiện, bấm **uploading an existing file**, kéo **toàn bộ file trong
   thư mục này** vào, rồi bấm **Commit changes**.
3. Vào tab **Settings** → mục **Pages** ở cột trái:
   - *Source*: **Deploy from a branch**
   - *Branch*: **main**, thư mục **/ (root)** → **Save**
4. Đợi 1–2 phút, địa chỉ sẽ là:
   `https://<tên-tài-khoản>.github.io/tracuu/`
5. Mở địa chỉ đó bằng **Chrome trên điện thoại** → menu ⋮ →
   **Thêm vào Màn hình chính** (có máy ghi là *Cài đặt ứng dụng*).

Xong. Từ đó bấm biểu tượng là vào thẳng, không cần trình quản lý file, không cần mạng
(lần đầu cần mạng để tải về, sau đó chạy ngoại tuyến).

## Khi có bản mới

Vào repo → **Add file** → **Upload files** → kéo lại các file mới (kéo cả 7 file cũng
được, GitHub tự ghi đè) → **Commit changes**.

Mở app trên điện thoại khi có mạng là nó tự lấy bản mới: `sw.js` để chế độ *ưu tiên
bản trên mạng, rớt mạng mới dùng bản đã lưu*, nên không phải sửa số phiên bản.

Chỉ khi nào **đổi biểu tượng hoặc manifest** thì mới cần mở `sw.js` sửa
`const PHIEN = 'tcdt-v1';` thành `'tcdt-v2'` để máy nạp lại bộ file đã lưu.

## Các file trong thư mục

| File | Việc |
|---|---|
| `index.html` | toàn bộ công cụ, không phụ thuộc gì bên ngoài |
| `manifest.webmanifest` | tên, màu, biểu tượng khi cài ra màn hình chính |
| `sw.js` | bộ nhớ đệm để mở được khi không có mạng |
| `icon-192.png`, `icon-512.png`, `icon-maskable-512.png` | biểu tượng |

## Lưu ý riêng tư

Repo công khai nghĩa là ai có đường dẫn đều xem được **mã nguồn công cụ**. Trong đó
không có thửa đất, không có tên khách hàng, không có file `.dgn` nào — bản đồ vẫn nằm
trong máy và chỉ được đọc lúc chạy. Riêng ảnh vệ tinh nền thì vẫn phải tải ô ảnh của
khu vực đang xem về, như trước.
