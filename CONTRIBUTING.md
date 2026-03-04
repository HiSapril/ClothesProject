# 🤝 Hướng dẫn Đóng góp (Contributing to Outfit AI)

Cảm ơn bạn đã quan tâm đến việc đóng góp cho dự án Outfit AI! Chúng tôi luôn hoan nghênh các cải tiến về tính năng, sửa lỗi và cải thiện tài liệu.

## 🚀 Thiết lập Môi trường Phát triển

1. **Khởi chạy các dịch vụ phụ trợ**:
   Dùng Docker để khởi động Postgres và Redis một cách nhanh nhất:
   ```bash
   docker-compose up -d db redis
   ```

2. **Cài đặt Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy API Server (Reload mode)**:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Quy chuẩn Kiểm thử (Testing)

Chúng tôi coi trọng tính ổn định. Mọi Pull Request đều phải vượt qua bộ test hiện tại.

- **Chạy toàn bộ test**:
  ```bash
  python -m pytest tests/
  ```

- **Khi thêm tính năng mới**:
  Vui lòng bổ sung test tương ứng trong thư mục `tests/` để đảm bảo không có lỗi phát sinh sau này.

## 🧱 Quy chuẩn Code Style

- Sử dụng **PEP 8** cho mã nguồn Python.
- Tên biến và hàm phải mang tính mô tả rõ ràng.
- Bổ sung Type Hints cho các hàm API và Service mới.

## 📬 Quy trình gửi Pull Request (PR)

1. Tạo một nhánh (branch) mới từ `main`.
2. Thực hiện thay đổi và đảm bảo code đã được format sạch sẽ.
3. Chạy lại bộ test (`pytest`).
4. Gửi PR và mô tả chi tiết những gì bạn đã thay đổi/cải thiện.

## 🎯 Code Owners
Mọi thay đổi liên quan đến cấu trúc cốt lõi (Core Architecture) hoặc AI Logic cần được review bởi Code Owners được chỉ định trong tệp `.github/CODEOWNERS`.

---
*Chúc bạn có trải nghiệm lập trình thú vị với Outfit AI!*
