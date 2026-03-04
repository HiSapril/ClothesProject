# 🚀 Hướng dẫn tích hợp Frontend (Frontend Quickstart)

Chào mừng bạn đến với dự án **Outfit AI**! Tài liệu này giúp bạn (người mới bắt đầu hoặc dev frontend) có thể chạy hệ thống và kết nối với Backend chỉ trong vài phút.

## 📋 Yêu cầu hệ thống
- **Docker & Docker Compose**: Để chạy toàn bộ hệ thống (API, Database, AI Worker, Redis) mà không cần cài đặt lẻ tẻ.
- **Trình duyệt**: Chrome, Edge hoặc Firefox.

---

## 🛠️ Bước 1: Khởi nguồn hệ thống

1. **Clone project**:
   ```bash
   git clone <repository_url>
   cd ClothesProject
   ```

2. **Cấu hình biến môi trường (.env)**:
   Tạo tệp `.env` tại thư mục gốc với nội dung sau:
   ```env
   # API Keys (Bắt buộc để chạy mượt mà)
   OPENWEATHER_API_KEY=your_key_here  # Lấy miễn phí tại openweathermap.org
   
   # Database & Redis (Dùng mặc định cho local)
   DATABASE_URL=postgresql://user:pass@db:5432/outfit_db
   REDIS_URL=redis://redis:6379/0
   
   # JWT Security
   SECRET_KEY=dev_secret_key_123
   ```
   *Lưu ý: Bạn có thể bỏ qua Google Calendar Key nếu chỉ muốn dùng các tính năng cơ bản.*

3. **Chạy Docker**:
   ```bash
   docker-compose up -d
   ```
   Hệ thống sẽ mất khoảng 1-2 phút ở lần đầu để tải AI Model.

---

## 🌐 Bước 2: Truy cập Giao diện
Mở trình duyệt và truy cập: `http://localhost:8000`

Hệ thống sẽ tự động chuyển hướng bạn đến trang đăng nhập/đăng ký. Hãy tạo một tài khoản mới để bắt đầu.

---

## 🧩 Bước 3: Cách Frontend nói chuyện với Backend

Toàn bộ logic kết nối được gói gọn trong `app/static/js/api.js`. Đây là 3 luồng chính bạn cần biết:

### 1. Luồng Tải ảnh & Xử lý (Async Upload)
Vì AI cần thời gian để "nhìn" ảnh, việc tải ảnh diễn ra theo 3 bước:
1. **Upload**: Gọi `POST /api/v1/items/upload` -> Nhận về `task_id`.
2. **Polling**: Thỉnh thoảng hỏi Backend: "Xong chưa?" qua `GET /api/v1/items/task/{task_id}`.
3. **Finish**: Khi status là `SUCCESS`, ảnh sẽ xuất hiện trong tủ đồ của bạn.

### 2. Luồng Gợi ý trang phục (Recommendation)
Gọi `POST /api/v1/recommend` kèm tọa độ vị trí (lat/lon). Backend sẽ tự lấy thời tiết và chọn đồ phù hợp nhất.

### 3. Khám phá Enums (Metadata)
Đừng hardcode danh sách loại quần áo! Hãy gọi `GET /api/v1/meta/enums` để lấy danh sách mới nhất từ Backend.

---

## 🏥 Kiểm tra trạng thái
Bạn có thể xem hệ thống "khỏe" hay không tại góc dưới cùng bên phải của giao diện Demo, hoặc truy cập trực tiếp:
`http://localhost:8000/api/v1/admin/readiness`

---

## 💡 Câu hỏi thường gặp (FAQ)
- **Q: Tại sao ảnh tôi tải lên báo Failed?**
  - *A: Có thể ảnh quá mờ hoặc không chứa quần áo rõ ràng. Thử dùng ảnh chụp sản phẩm trên nền trắng.*
- **Q: Tôi không có Google Calendar key có sao không?**
  - *A: Không sao cả! Hệ thống sẽ dùng thời tiết và các sự kiện bạn nhập thủ công để gợi ý đồ.*
