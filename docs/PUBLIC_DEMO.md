# 🌟 Hướng dẫn Trải nghiệm Demo Public (Public Demo Guide)

Chào mừng bạn đến với bản demo trực tuyến của **Outfit AI**! Đây là trợ lý thời trang thông minh được xây dựng để giúp bạn quản lý tủ đồ và phối đồ dựa trên thời tiết và sự kiện.

## 🔗 Cách truy cập
- **Địa chỉ**: `http://<your-demo-url>` (Nếu bạn đang chạy local, hãy dùng `http://localhost:8000`)
- **Tài khoản Demo**: Nếu hệ thống đang ở chế độ `DEMO_MODE`, bạn có thể nhấn vào nút "Dùng thử với tư cách Khách" (Guest login) để trải nghiệm ngay mà không cần đăng ký.

---

## 🎯 Các tính năng cốt lõi cần thử
1. **Quản lý Tủ đồ**: Tải lên ảnh quần áo của bạn. AI sẽ tự động tách nền và phân loại trang phục.
2. **Gợi ý Thông minh**: Nhấn "Gợi ý trang phục" để AI đề xuất các bộ phối hợp lý nhất cho ngày hôm nay.
3. **Theo dõi Trạng thái**: Quan sát quá trình AI xử lý ảnh theo thời gian thực (Queued -> Processing -> Completed).

---

## 🔒 Hạn chế của bản Demo
Để đảm bảo sự ổn định cho mọi người dùng, bản demo có một số giới hạn:
- **Tốc độ (Rate Limit)**: Bạn có thể bị tạm dừng nếu thực hiện quá 10 yêu cầu gợi ý trong 1 phút.
- **Dữ liệu (Data Reset)**: Dữ liệu trong bản demo có thể bị xóa sạch mỗi 24 giờ để làm sạch hệ thống.
- **Xử lý AI**: Bản demo sử dụng mô hình AI nhẹ để đảm bảo tốc độ phản hồi nhanh.

---

## 🏗️ Kiến trúc Hệ thống (Dành cho nhà tuyển dụng/Reviewer)
Hệ thống được thiết kế theo chuẩn sản phẩm thực tế:
- **Backend**: FastAPI (Python) - Hiệu năng cao, kiến trúc rõ ràng.
- **Xử lý ngầm**: Celery & Redis - Đảm bảo các tác vụ AI không làm treo web.
- **Cơ sở dữ liệu**: PostgreSQL - Lưu trữ bền vững và tin cậy.
- **Ops**: Sẵn sàng triển khai Docker, có tích hợp giám sát sức khỏe (Healthcheck) và Versioning.

---

## 🛡️ Cam kết Tin cậy
Hệ thống được tích hợp cơ chế tự phục hồi. Nếu có bất kỳ lỗi nào xảy ra trong quá trình xử lý AI, bạn sẽ nhận được thông báo chi tiết và nút "Thử lại" nếu lỗi đó có thể khắc phục được.

---
*Cảm ơn bạn đã trải nghiệm Outfit AI!*
