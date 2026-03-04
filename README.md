# 👕 Outfit AI - Personal Fashion Assistant

![CI Status](https://github.com/HiSapril/ClothesProject/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10-blue)
![Docker Ready](https://img.shields.io/badge/docker-ready-green)
![License](https://img.shields.io/badge/license-MIT-purple)

Hệ thống trợ lý thời trang cá nhân thông minh, giúp bạn quản lý tủ đồ và nhận gợi ý trang phục dựa trên thời tiết và sự kiện.

## 🎯 Bài toán & Giá trị (Problem Statement)
Hệ thống giải quyết khó khăn trong việc lựa chọn trang phục hàng ngày bằng cách tự động hóa quy trình:
1. **Tiết kiệm thời gian**: Không còn phải phân vân "hôm nay mặc gì?".
2. **Tối ưu hóa tủ đồ**: Gợi ý phối đồ từ những món đồ bạn đã sở hữu, tránh lãng phí.
3. **Thích ứng môi trường**: Luôn mặc đúng nhờ tích hợp thời tiết và lịch trình thời gian thực.

---

## 🌟 Tính năng (Features)
- **Thiên văn máy tính (Computer Vision)**: Tự động tách nền (`rembg`) và phân loại quần áo bằng AI (`ResNet50`).
- **Tương tác ngữ cảnh (Context Aware)**: Tích hợp OpenWeatherMap (thời tiết) & Google Calendar (lịch trình).
- **Gợi ý thông minh (Smart Recommendations)**: Công cụ lọc và phối đồ dựa trên thuộc tính và quy tắc thời trang.
- **Tủ đồ cá nhân**: Lưu trữ và tổ chức trang phục cá nhân với tính năng deduplication bằng hình ảnh.
- **Hiệu suất & Bộ nhớ**: Tích hợp Redis để cache thời tiết và kết quả gợi ý.

## 🏗️ Kiến trúc hệ thống (Architecture)

```mermaid
graph TD
    User([Người dùng]) --> API[FastAPI API]
    API --> DB[(PostgreSQL)]
    API --> Redis[(Redis Cache/Queue)]
    Redis <--> Worker[Celery Worker]
    Worker --> AI[AI Engine: ResNet50]
    API --> Weather[OpenWeather API]
    API <--> Cal[Google Calendar API]
```

---

## 🛠️ Hướng dẫn cài đặt (Setup Instructions)

### 1. Yêu cầu hệ thống (Prerequisites)
- **Python**: Phiên bản 3.10 trở lên.
- **PostgreSQL**: Đã được cài đặt và đang chạy.
- **Google Cloud Console**: Nếu muốn sử dụng tính năng đồng bộ lịch (Calendar).

### 2. Cấu hình môi trường (Environment Configuration)
Tạo file `.env` trong thư mục gốc của dự án (dựa trên mẫu dưới đây hoặc từ `app/core/config.py`):

```env
DATABASE_URL=postgresql://postgres:user_password@localhost:5432/clothes_db
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

*Lưu ý: Thay `user_password` và `clothes_db` bằng thông tin thực tế của bạn.*

### 3. Cài đặt nhanh trên Windows (Quick Start)
Dự án đã có sẵn file script để tự động thực hiện các bước cài đặt và khởi chạy:
- Chạy file `run_project.bat` bằng cách nhấp đúp hoặc chạy trong Terminal:
  ```cmd
  ./run_project.bat
  ```
  Script này sẽ tự động:
  1. Tạo môi trường ảo (venv).
  2. Cài đặt các thư viện cần thiết (bypass các lỗi SSL phổ biến).
  3. Khởi tạo Database.
  4. Chạy Server.

### 4. Cài đặt thủ công (Manual Setup - Linux/macOS)
Nếu bạn không dùng Windows, hãy thực hiện các bước sau:
```bash
# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Trên Linux/macOS
# venv\Scripts\activate  # Trên Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi tạo database
export PYTHONPATH=.
python scripts/init_db.py

# Chạy server
uvicorn app.main:app --reload
```

### 5. Triển khai bằng Docker (Production-ready)
Dự án được tối ưu hóa để chạy trong container:
```bash
# 1. Tạo file .env từ template
cp .env.example .env

# 2. Khởi chạy toàn bộ hệ thống
docker-compose up -d --build
```
Hệ thống Docker bao gồm:
- **`api`**: FastAPI server xử lý request.
- **`worker`**: Celery xử lý AI offline.
- **`redis`**: Broker cho tasks và Cache.
- **`db`**: Database PostgreSQL lưu trữ dữ liệu.

### 6. Chạy Tests (Manual Setup)
```bash
export PYTHONPATH=.
python -m pytest tests/ --verbose
```

---

## 📅 Tích hợp Google Calendar (Tùy chọn)
Để sử dụng tính năng gợi ý theo sự kiện:
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/).
2. Tạo dự án, bật **Google Calendar API**.
3. Tạo **OAuth 2.0 Client ID** và tải file `credentials.json` về.
4. Đặt file `credentials.json` vào thư mục gốc của dự án.
5. Sau khi chạy server, truy cập `/api/v1/calendar/login` để kết nối tài khoản.

---

## 📱 Sử dụng API (API Usage)

Sau khi server chạy, bạn có thể truy cập tài liệu API tự động tại:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 7. Portfolio Demo Flow
Nếu bạn muốn trải nghiệm nhanh các tính năng chính (Demo):
1. **Đăng ký**: `POST /api/v1/auth/register`
2. **Tải đồ**: `POST /api/v1/items/upload` (Chọn ảnh một chiếc áo hoặc quần).
3. **Xử lý AI**: Đợi task status đạt `completed`.
4. **Gợi ý**: `POST /api/v1/recommend` với tọa độ thực tế để nhận outfit phối đồ bài bản.

---

## 📈 Lộ trình sản phẩm (Product Roadmap)
- **v1.0 (Stable)**: Backend cốt lõi, AI processing, Security, Caching, Docker ready.
- **v1.1**: Administrative Observability & Deep health checks.
- **v2.0 (Planned)**: Mobile App (React Native), Social sharing, và AI phối đồ nâng cao.

## 🚢 Hướng dẫn triển khai (Deployment Guide)

### Triển khai trên VPS (UBUNTU/DEBIAN)
1. **Cài đặt Docker & Nginx**:
   ```bash
   sudo apt update && sudo apt install docker-compose nginx -y
   ```
2. **Reverse Proxy (Nginx Config)**:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header X-Request-ID $request_id;
       }
   }
   ```
3. **HTTPS**: Sử dụng `Certbot` để kích hoạt SSL.

### Cloud Ready (AWS/GCP)
- Sử dụng **Managed Postgres** (RDS/Cloud SQL) và **Elasticache** (Redis).
- Chạy API/Worker trên **ECS/Kubernetes** hoặc **App Engine**.

---

## 📂 Cấu trúc dự án (Project Structure)
- `app/`: Mã nguồn chính (FastAPI).
- `app/api/admin_ops.py`: Quản trị & Giám sát hệ thống.
- `scripts/`: Các script hỗ trợ (khởi tạo DB, migrate).
- `tests/`: Bộ test suite tự động (pytest).
- `Dockerfile` & `docker-compose.yml`: Cấu hình container hóa.

---

## 🎨 Hướng dẫn tích hợp Frontend (Frontend Integration Guide)

### 1. Luồng tải ảnh & Xử lý AI (Upload → Poll)
Do quá trình xử lý AI tốn thời gian, hệ thống sử dụng cơ chế bất đồng bộ:
1. **Upload**: `POST /api/v1/items/upload`
   - Trả về `task_id` và `item_id`.
   - **Idempotency**: Nếu upload cùng một file ảnh, hệ thống trả về kết quả cũ thay vì tạo mới.
2. **Poll**: `GET /api/v1/items/task/{task_id}`
   - Kiểm tra trạng thái cho đến khi `status == 'SUCCESS'`.
3. **Finish**: Khi `status` của item là `COMPLETED`, item đó đã sẵn sàng để được gợi ý.

### 2. Vòng đời Task & Item (Lifecycle)
**Task States (Celery):**
- `PENDING`: Đang chờ xử lý.
- `STARTED`: Đang được worker thực hiện.
- `SUCCESS`: Hoàn thành thành công.
- `FAILURE`: Gặp lỗi trong quá trình xử lý.

**Item Status (ClothingItem):**
- `QUEUED`: Đã đăng ký, chờ AI.
- `PROCESSING`: Đang chạy AI logic.
- `COMPLETED`: Ảnh đã được xử lý và phân loại.
- `FAILED`: Không thể xử lý ảnh (ví dụ: không tìm thấy quần áo).

### 3. Xử lý Lỗi chuẩn hóa
Mọi lỗi trả về định dạng JSON:
```json
{
  "error_code": "STRING_CODE",
  "message": "Human readable message",
  "request_id": "uuid-v4",
  "retry_after": 60 (Tùy chọn cho lỗi 429)
}
```

### 4. Khám phá Metadata
Sử dụng `GET /api/v1/meta/enums` để lấy danh sách các category, occasion và role hợp lệ, giúp UI đồng bộ với Backend mà không cần hardcode string.

---

## ️ Độ tin cậy & Vận hành (System Health & Reliability)

### 1. Giám sát trạng thái (Health Checks)
Hệ thống cung cấp các endpoint chuyên biệt cho việc vận hành:
- **Liveness/Readiness**: `GET /api/v1/admin/readiness`
  - Kiểm tra kết nối Database, Redis và trạng thái Celery Worker.
  - Phù hợp cho Docker Compose `healthcheck` hoặc Kubernetes `probes`.
- **Versioning**: `GET /api/v1/admin/version`
  - Trả về thông tin build, git commit và API version hiện tại.

### 2. Xử lý lỗi & Tự phục hồi (Failure Recovery)
- **AI Task Timeout**: Celery được cấu hình giới hạn thời gian (30s soft, 45s hard). Nếu AI xử lý quá lâu, task sẽ tự động bị hủy và đánh dấu `FAILED` với lý do `AI timeout exceeded`.
- **Graceful Shutdown**: Khi dừng container, FastAPI sẽ hoàn tất các request đang xử lý và đóng kết nối Redis/DB một cách an toàn để tránh mất dữ liệu.
- **Retry Policy**: Các lỗi hệ thống (mất kết nối mạng tạm thời) sẽ trả về `retryable: true`. Các lỗi logic (ảnh không chứa quần áo) sẽ trả về `retryable: false`.

### 3. Bảo mật Startup
Hệ thống tự động kiểm tra cấu hình Database và Redis ngay khi khởi động. Nếu các dịch vụ lõi không khả dụng, API sẽ log cảnh báo `CRITICAL` để quản trị viên xử lý kịp thời.

---

## 📖 Hướng dẫn cho người mới (Frontend Developers)
👉 **[Xem tài liệu tích hợp Frontend & Hướng dẫn chạy nhanh](docs/FRONTEND_QUICKSTART.md)**

---

## 🏷️ Chính sách Phiên bản API (API Versioning Policy)
Hệ thống tuân thủ nguyên tắc ổn định cho người dùng cuối:
- **v1 (Hiện tại)**: Phiên bản ổn định, hỗ trợ đầy đủ các tính năng tủ đồ và gợi ý.
- **v2 (Kế hoạch)**: Sẽ được giới thiệu khi có các thay đổi phá vỡ cấu trúc (breaking changes) như thay đổi logic AI core.
- **Thông tin phiên bản**: Có thể kiểm tra tại `GET /api/v1/admin/version`.

---

---

## 🧠 Cách Outfit AI ra quyết định (Decision Engine)
Khác với các hệ thống AI thông thường chỉ đưa ra dự đoán nhãn, Outfit AI sở hữu một **Decision Layer** thông minh:
- **Decision vs Prediction**: Hệ thống không tin tưởng mù quáng vào model. Nó áp dụng các ngưỡng an toàn để quyết định khi nào cần sự xác nhận của người dùng.
- **Explainability (XAI)**: Mọi gợi ý trang phục đều có lý do rõ ràng (ví dụ: "Vì hôm nay 15°C...").
- **Failure Intelligence**: Khi không thể xử lý, hệ thống đưa ra mã lỗi (typed failures) kèm hành động gợi ý cụ thể để giúp người dùng thành công ở lần sau.

👉 **[Khám phá chi tiết Bộ não quyết định của Outfit AI](docs/AI_DECISION_ENGINE.md)**

---

## 🤖 Trí tuệ AI & Đánh giá (AI Intelligence & Evaluation)
Hệ thống không chỉ là một API đơn thuần; nó được xây dựng trên nền tảng **MLOps readiness**:
- **Model Contract**: Mọi suy luận AI đều tuân thủ một bộ quy tắc nghiêm ngặt về độ tin cậy (Confidence threshold). 
- **Đánh giá Hiệu năng**: Chúng tôi đo lường độ chính xác của mô hình thông qua bộ dữ liệu kiểm soát (Ground Truth).
- **Khả năng tái lập**: Pipeline tiền xử lý và đánh giá được đóng gói hoàn toàn trong Docker.

👉 **[Xem chi tiết Hợp đồng AI & Thông số Mô hình](docs/AI_MODEL.md)**

### Cách chạy đánh giá AI (AI Evaluation)
Để kiểm tra độ chính xác của hệ thống trên môi trường Docker:
```bash
docker-compose --profile ai-eval up
```
Kết quả sẽ được ghi vào tệp `evaluation_results.json`.

---

## 🛡️ Cam kết Chất lượng (Quality Guarantees)
Dự án được xây dựng với tư duy "Engineering Excellence":
- **Kiểm thử tự động**: 100% các tính năng cốt lõi (Auth, RBAC, AI Workflow, Recommendation) đều có unit/integration tests (`pytest`).
- **CI/CD**: Luôn chạy bộ test tự động trên GitHub Actions trước khi merge code vào `main`.
- **An toàn Operational**: Tích hợp Healthcheck, Versioning, và Logging có cấu trúc để dễ dàng debug trong production.

---

## 🤝 Hướng dẫn Đóng góp (Contributor Guide)
Chúng tôi luôn hoan nghênh sự đóng góp từ cộng đồng!
- 🛠️ **[Tài liệu hướng dẫn Đóng góp](CONTRIBUTING.md)** (Local Setup, Branching, PR rules).
- 🏷️ **[Chính sách Phiên bản](docs/VERSIONING.md)** (SemVer, API vs App versions).

---

## 🏗️ Xử lý sự cố (Troubleshooting)

| Vấn đề | Giải pháp |
| :--- | :--- |
| **Lỗi kết nối Redis** | Đảm bảo service Redis đang chạy (Port 6379). Trong Docker, dùng `docker-compose logs redis`. |
| **Ảnh không xử lý** | Kiểm tra Celery worker: `docker-compose logs worker`. |
| **Lỗi Database** | Chạy migrations: `alembic upgrade head`. |
| **Lỗi Rate Limit** | Đây là tính năng bảo mật. Nếu bị chặn, hãy đợi 60 giây. |

---
*Lưu ý: Các file nhạy cảm như `.env`, `credentials.json` và thư mục `venv` đã được loại bỏ khi đẩy lên GitHub theo cấu hình trong `.gitignore`.*
