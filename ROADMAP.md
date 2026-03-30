# ROADMAP TINH NANG DESKTOP - ANDROID - KHACH HANG

Cap nhat lan cuoi: 2026-03-30
Trang thai: Ban mo rong (co the tiep tuc bo sung)

## 1) Muc tieu tong

Xay dung luong thanh toan lien thong giua Desktop, Android va Khach hang:
- Desktop tao ghi chu, chon san pham, tinh tong tien.
- Desktop tao link thanh toan VietQR (dang text), gui sang Android.
- Android hien thi QR (render cuc bo) hoac gui link cho khach.
- Khach bam link, quet QR bang app ngan hang, chuyen khoan.
- Android bat notification giao dich, so khop so tien + ma ghi chu.
- Android goi API desktop de tu dong hoan thanh ghi chu.

## 2) Luong nghiep vu chuan

Desktop                        Android                          Khach hang
|                              |                                |
| Tao ghi chu + chon SP        |                                |
| -> tinh tong tien            |                                |
|                              |                                |
| Nhan [Tao link thanh toan]   |                                |
| -> sinh URL VietQR           |                                |
| -> POST /api/qr-invoice      |                                |
| ---------------------------> |                                |
|                              | Nhan link + hien QR cuc bo     |
|                              | (hoac gui link cho khach)      |
|                              | -----------------------------> |
|                              |                                |
|                              |                         Bam link -> thay QR
|                              |                         -> quet bang app bank
|                              |                         -> chuyen khoan
|                              |                                |
|                              | Bat notification ngan hang     |
|                              | -> so khop so tien + ma GC     |
|                              | -> match ghi chu               |
|                              |                                |
| POST /api/notes/{id}/complete|                                |
| <--------------------------- |                                |
|                              |                                |
| Tu dong hoan thanh ghi chu   |                                |

## 3) Pham vi thong tin can co trong don thanh toan

Moi don thanh toan can co day du:
- note_id: ID ghi chu.
- note_code: Ma doi soat, de xuat dang GC{note_id}.
- customer_name: Ten khach (neu co).
- phone: SDT khach (neu co).
- items: Danh sach san pham da mua.
- subtotal: Tong tien hang truoc dieu chinh.
- discount: Giam gia (neu co).
- shipping_fee: Phi ship (neu co).
- final_amount: So tien cuoi cung can thanh toan.
- transfer_content: Noi dung chuyen khoan khuyen nghi (VD: GC42).
- vietqr_url: Link text thanh toan.
- expire_at: Han thanh toan cua link (neu ap dung).
- payment_status: pending, matched, completed, failed.

### Cau truc items de xuat

- product_id
- product_name
- unit
- qty
- unit_price
- line_total
- note

## 4) Tinh nang moi bo sung theo yeu cau

### 4.1 Hien thi san pham da mua

Desktop:
- Trong TaskDialog/ghi chu: cho chon nhieu san pham.
- Hien thi bang tam tinh theo dong san pham.
- Tu dong cap nhat subtotal/final_amount.
- Luu danh sach items vao DB theo note_id.

Android:
- Khi nhan payload /api/qr-invoice: hien thi tom tat san pham.
- Hien thi tong tien va ma doi soat.
- Cho copy nhanh noi dung don hang + link thanh toan.

Khach hang:
- Nhan duoc text co thong tin don + link thanh toan.
- Neu can, nhan them danh sach san pham dang text ngan gon.

### 4.2 Them thong bao ghi chu cua app

Muc tieu:
- App Android co thong bao ro rang cho cac su kien ghi chu.

Su kien thong bao de xuat:
- Tao ghi chu moi thanh cong.
- Da tao link thanh toan.
- Da gui link cho khach.
- Phat hien giao dich phu hop ghi chu.
- Tu dong hoan thanh ghi chu thanh cong.
- Loi so khop/khong du dieu kien so khop.
- Link qua han hoac thanh toan that bai.

Kenh thong bao:
- In-app banner (uu tien).
- Android notification (co channel rieng: Notes/Payments).
- Log lich su su kien trong man hinh Notes.

## 5) API roadmap

### 5.1 Desktop API can them

1. POST /api/qr-invoice
- Input: note_id, items, final_amount, transfer_content
- Output: success, vietqr_url, qr_payload, expire_at

2. POST /api/notes/{id}/complete
- Input: matched_amount, matched_content, source, tx_time
- Output: success, note_status

3. GET /api/notes/{id}/invoice
- Output: thong tin don va danh sach items

4. GET /api/notes/pending-payments
- Output: danh sach ghi chu dang cho thanh toan

5. POST /api/notes/{id}/events
- Input: event_type, message, metadata
- Output: success

### 5.2 Android API su dung

- Goi /api/qr-invoice de dong bo payload.
- Goi /api/notes/{id}/complete khi match thanh cong.
- Goi /api/notes/{id}/events de day lich su thong bao.

## 6) Logic so khop thanh toan

Thu tu uu tien khi match:
1. Match note_code (GCxx) + amount chinh xac.
2. Match note_code neu amount sai lech nho trong nguong cho phep.
3. Match amount FIFO neu khong co note_code.
4. Khong match -> dua vao hang cho duyet tay.

Nguong sai lech de xuat:
- amount_tolerance = 1000 VND.

Dieu kien an toan:
- Moi giao dich chi duoc su dung de complete 1 ghi chu.
- Co co che idempotency key tranh complete lap.
- Luu transaction fingerprint de tranh trung.

## 7) UI/UX roadmap

### Desktop
- Nut Tao link thanh toan trong man ghi chu.
- Preview text gui khach truoc khi copy/gui.
- Hien thi danh sach san pham da mua ngay tren card ghi chu.
- Badge trang thai: Cho thanh toan / Da match / Da hoan thanh / Loi.
- Timeline su kien cua ghi chu.

### Android
- Man hinh Notes: co section Payment Requests.
- Sheet hien QR + thong tin don + san pham.
- Nut Chia se link nhanh: Zalo, SMS, copy.
- Notification channel rieng cho Note Payment.
- Lich su thong bao va ket qua so khop.

## 8) Ke hoach trien khai theo phase

### Phase 1 - Nen tang du lieu va API (1-2 tuan)
- Tao bang invoice_items gan voi note_id.
- Tao endpoint /api/qr-invoice, /api/notes/{id}/complete.
- Them event log cho notes.
- Them migration + test API co ban.

### Phase 2 - Desktop tao don va tao link (1 tuan)
- UI chon san pham trong ghi chu.
- Tinh tong tien, sinh transfer_content.
- Tao vietqr_url va copy text gui khach.
- Hien thi san pham da mua trong ghi chu.

### Phase 3 - Android tiep nhan va thong bao (1 tuan)
- Hien thi payload thanh toan.
- Hien thi QR cuc bo tu URL/payload.
- Them thong bao app cho cac su kien ghi chu.
- Them lich su su kien ghi chu tren Android.

### Phase 4 - Auto match va auto complete (1 tuan)
- Bat notification bank.
- So khop amount + note_code.
- Goi API complete + cap nhat UI 2 dau.
- Xu ly truong hop khong match.

### Phase 5 - On dinh va mo rong (1-2 tuan)
- Retry queue khi mat mang.
- Dashboard thong ke ti le match.
- Rule nang cao cho trung so tien.
- Toi uu toc do va trai nghiem.

## 9) Tieu chi nghiem thu

Bat buoc:
- Tao ghi chu co items va tong tien dung.
- Tao link thanh toan text hop le.
- Khach bam link va thanh toan duoc.
- Android nhan notification va match dung.
- Desktop tu dong complete dung ghi chu.
- Co log su kien day du va truy vet duoc.

Hieu nang:
- Thoi gian tu luc co notification den luc complete < 3 giay (muc tieu).

Do tin cay:
- Match sai <= 0.1% tren tap test noi bo.

## 10) Backlog mo rong

- Hoan tien 1 phan/nhieu lan cho 1 ghi chu.
- Chia bill theo nhieu nguoi nhan link.
- QR dong (co han ngắn, token ky so).
- Cho phep de lai coc truoc.
- Ket noi them cong thanh toan khac ngoai bank transfer.
- Nhac no tu dong cho ghi chu qua han.
- Bao cao doanh thu theo kenh thanh toan.
- Web mini page cho khach xem lai chi tiet don.

## 11) Rui ro va giam thieu

- Khach khong ghi dung noi dung chuyen khoan:
  Giai phap: uu tien note_code, fallback amount + FIFO + duyet tay.

- Trung amount giua nhieu don:
  Giai phap: bat buoc transfer_content chua ma GC.

- Notification ngan hang thay doi format:
  Giai phap: parser da nguon + bo regex co cau hinh.

- Mat ket noi tam thoi:
  Giai phap: retry queue + idempotency.

- Hoan thanh nham ghi chu:
  Giai phap: event log day du + rollback 1 buoc trong admin.

## 12) Danh sach viec can lam ngay (next actions)

1. Chot data model invoice_items va note_events.
2. Tao endpoint /api/qr-invoice tren desktop.
3. Bo sung transfer_content = GC{note_id}.
4. Cap nhat TaskDialog de them danh sach san pham da mua.
5. Them Notification channel Notes/Payments tren Android.
6. Viet bo test integration cho luong complete tu dong.
