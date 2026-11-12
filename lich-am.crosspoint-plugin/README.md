# Lịch Âm Dương

Đặt **lịch tháng tiếng Việt có âm lịch** lên màn hình ngủ của máy đọc: ngày âm
dưới mỗi ngày dương, hôm nay được tô đen, ngày lễ được đóng khung, chân trang
ghi ngày âm, can chi và các ngày lễ sắp tới trong tháng.

## Cài đặt

Cài *Lịch Âm Dương* từ Plugin Hub, hoặc chép thư mục này vào
`/.crosspoint/plugins/lich-am/` trên thẻ SD, bật plugin trong Cài đặt rồi khởi
động lại máy. Đặt màn hình ngủ ở chế độ **CUSTOM**.

## Cách hoạt động

Mỗi lần ngủ, máy tải `current.bmp` (BMP 1-bit, 480×800) về `/sleep.bmp`. Ảnh
được GitHub Actions vẽ lại mỗi ngày lúc 0h giờ Việt Nam. Cần WiFi (pin ≥ 20% và
có mạng đã lưu); nếu tải lỗi thì giữ ảnh cũ.
