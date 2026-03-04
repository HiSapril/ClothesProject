# 🏷️ Chính sách Phiên bản (Versioning Policy)

Dự án Outfit AI sử dụng quy tắc **Semantic Versioning (SemVer)** để quản lý các thay đổi và đảm bảo tính tương thích.

## 🔢 Cấu trúc Phiên bản: `MAJOR.MINOR.PATCH`

1. **MAJOR (Số chính)**: Thay đổi khi có các cập nhật phá vỡ tính tương thích (breaking changes) với API hiện tại hoặc cấu trúc dữ liệu cốt lõi.
2. **MINOR (Số phụ)**: Thay đổi khi thêm tính năng mới mà vẫn giữ được tính tương thích ngược (backward compatible).
3. **PATCH (Số vá lỗi)**: Thay đổi khi thực hiện các bản vá lỗi nhỏ, tối ưu hiệu năng hoặc cập nhật tài liệu.

## 🌐 Mối quan hệ giữa App Version và API Version

- **App Version (vd: 1.2.2)**: Đại diện cho toàn bộ trạng thái của Repository (bao gồm Frontend, Backend, và Docs).
- **API Version (vd: /api/v1)**: Đại diện cho hợp đồng giao tiếp giữa Client và Server. Một API version có thể tồn tại qua nhiều App versions miễn là cấu trúc request/response không thay đổi.

## 🔄 Quy trình nâng cấp
- Mọi thay đổi về version phải được phản ánh trong `app/api/admin_ops.py` thông qua endpoint `/admin/version`.
- Lịch sử thay đổi đáng chú ý sẽ được ghi lại trong tệp `CHANGELOG.md` (nếu có).
