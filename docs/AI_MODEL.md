# 🧠 AI Model Specification & Inference Contract

Tài liệu này định nghĩa các tiêu chuẩn kỹ thuật cho mô hình AI được sử dụng trong dự án **Outfit AI**.

## 🚀 Thông tin Mô hình
- **Phiên bản**: `v1.0-resnet50`
- **Kiến trúc**: ResNet50 (Transfer Learning)
- **Tiền xử lý**: `rembg` (Remove Background) + Resize (224x224)
- **Đầu ra**: 8 phân loại thời trang (Top, Bottom, Shoes, etc.)

---

## 📝 Hợp đồng Inference (Inference Contract)

### 1. Đầu vào (Input)
- **Định dạng**: Ảnh (JPEG, PNG).
- **Kích thước tối đa**: 5MB.
- **Yêu cầu**: Ảnh nên chứa một sản phẩm may mặc rõ ràng trên nền đơn sắc (để đạt độ chính xác cao nhất).

### 2. Đầu ra (Output)
Hệ thống trả về đối tượng JSON:
```json
{
  "category": "string",
  "confidence": "float (0.0 - 1.0)",
  "processing_time": "float (seconds)"
}
```

---

## ⚖️ Quy tắc Diễn giải Độ tin cậy (Confidence Rules)

Để đảm bảo chất lượng gợi ý, chúng tôi áp dụng các ngưỡng sau:

| Ngưỡng (Confidence) | Trạng thái | Hành động hệ thống |
| :--- | :--- | :--- |
| **> 0.85** | High | Tự động phân loại và lưu vào tủ đồ. |
| **0.5 - 0.85** | Medium | Lưu vào tủ đồ nhưng đánh dấu "Cần kiểm tra lại". |
| **< 0.5** | Low | Đánh dấu "Thất bại" (Unknown Category) để bảo vệ tính chính xác của dữ liệu. |

---

## 📊 Đánh giá & Giám sát (Evaluation)
Chúng tôi duy trì một bộ dữ liệu kiểm soát (Ground Truth) tại `datasets/sample_labels.json`.
Bạn có thể chạy đánh giá hiệu năng mô hình bằng lệnh:
```bash
docker-compose --profile ai-eval up
```

Mục tiêu hiệu năng tối thiểu cho môi trường Production:
- **Accuracy**: > 92%
- **Latency**: < 2.0s per image
