# 🧠 Hệ thống Ra quyết định AI (AI Decision Engine)

Dự án **Outfit AI** không chỉ dừng lại ở việc dự đoán nhãn ảnh; nó sở hữu một tầng logic thông minh (Decision Layer) để đảm bảo mọi quyết định gửi tới người dùng đều an toàn, minh bạch và có thể giải thích được.

## 🏗️ Luồng xử lý Quyết định (Decision Pipeline)

Dữ liệu đi qua 3 giai đoạn chính:
1. **Model Inference**: ResNet50 đưa ra xác suất thô (Raw labels & Confidence).
2. **Intelligent Layer**: Áp dụng các ngưỡng an toàn (Thresholds) và quy tắc nghiệp vụ.
3. **Decisive Action**: Quyết định chấp nhận, đánh dấu cần xác nhận, hoặc từ chối kết quả.

---

## ⚖️ Quy tắc Nghiệp vụ (Deterministic Rules)

Hệ thống hoạt động dựa trên các ngưỡng xác định để đảm bảo tính nhất quán:

| Ngưỡng | Trạng thái (Decision) | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| **> 85%** | `CONFIRMED` | Tin cậy tuyệt đối, hệ thống tự động xử lý. |
| **50% - 85%** | `LOW_CONFIDENCE` | Tin cậy trung bình, yêu cầu người dùng xác xác nhận. |
| **< 50%** | `UNKNOWN` | Không an toàn, chuyển hướng sang xử lý lỗi thông minh. |

---

## 💬 Khả năng Giải thích (Explainability - XAI Lite)

Chúng tôi tin rằng "Sự tin tưởng đến từ sự thấu hiểu". Mỗi gợi ý trang phục đều đi kèm một lời giải thích deterministic:

- **Công thức**: `[Weather Context] + [Occasion Context] -> [Human Action]`
- **Ví dụ**: "Vì hôm nay trời lạnh (15°C) và bạn có buổi họp, chúng tôi ưu tiên phong cách nghiêm túc kết hợp áo khoác giữ ấm."

---

## ❌ Phân loại Lỗi Thông minh (Failure Taxonomy)

Thay vì thông báo "Lỗi" chung chung, hệ thống cung cấp mã lỗi định danh và hành động gợi ý:

1. **`LOW_CONFIDENCE`**: Ảnh quá mờ hoặc phông nền quá phức tạp.
   - *Gợi ý*: Chụp lại ảnh với ánh sáng tốt hơn.
2. **`INSUFFICIENT_WARDROBE`**: Tủ đồ không đủ category để phối đồ theo yêu cầu.
   - *Gợi ý*: Hãy thêm ít nhất một chiếc quần (Bottom) để nhận gợi ý.
3. **`CONFLICTING_CONTEXT`**: Thời tiết quá khắc nghiệt không phù hợp cho sự kiện yêu cầu.
   - *Gợi ý*: Kiểm tra lại địa điểm hoặc loại hình sự kiện.

---

## 📊 Chỉ số Quyết định (Decision Metrics)

Chúng tôi giám soát hiệu quả của tầng quyết định thông qua:
- **Acceptance Rate**: Tỷ lệ người dùng chấp nhận các phân loại `LOW_CONFIDENCE`.
- **Fallback Frequency**: Tần suất hệ thống phải từ chối ảnh do độ tin cậy thấp.
- **XAI Coverage**: Đảm bảo 100% gợi ý đều có giải thích đi kèm.
