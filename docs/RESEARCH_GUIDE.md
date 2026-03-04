# 🧪 Hướng dẫn Nghiên cứu & Đánh giá (Research Guide)

Tài liệu này hướng dẫn cách thực hiện các thí nghiệm so sánh và đánh giá khoa học dựa trên hệ thống **Outfit AI**.

## 🔬 Mục tiêu Nghiên cứu
So sánh định lượng và định tính giữa hai phương pháp tiếp cận chính:
1. **BASELINE**: Phối đồ dựa thuần túy trên phân loại danh mục quần áo.
2. **CONTEXT_AWARE**: Phối đồ có tính toán đến các yếu tố ngoại cảnh (Thời tiết, Sự kiện) và được giám sát bởi **Decision Layer**.

---

## 🛠️ Phương pháp thí nghiệm (Methodology)

Chúng tôi cung cấp khả năng điều khiển các biến số thí nghiệm qua API `/recommend`:

### 1. Biến số độc lập (Independent Variables)
- **Strategy**: `BASELINE` vs `CONTEXT_AWARE`.
- **Decision Layer**: `Enabled` (ON) vs `Disabled` (OFF).
- **Environmental Context**: Thông qua `context_override` (Nhiệt độ, Thời tiết).

### 2. Biến số phụ thuộc (Dependent Variables)
- **Recommendation Quality Score**: Điểm số do hệ thống tính toán (0-100).
- **Safety Violation Rate**: Tỷ lệ gợi ý vi phạm các quy tắc an toàn (VD: Áo khoác dày trong trời nóng).
- **Explainability Score**: Tính rõ ràng và hợp lý của lời giải thích đi kèm.

---

## 📊 Kịch bản Đánh giá (Evaluation Scenarios)

Sử dụng tập lệnh `scripts/research_eval.py` để chạy các tình huống kiểm soát:

1. **Hiệu quả của Decision Layer**:
   - So sánh output khi bật/tắt Decision Layer trong điều kiện thời tiết cực đoan (Nắng nóng > 35°C).
   - Kiểm chứng khả năng ngăn chặn các kết hợp áo khoác dày khi trời nóng.

2. **So sánh BASELINE vs CONTEXT_AWARE**:
   - Đánh giá mức độ phù hợp của trang phục khi có sự thay đổi về sự kiện (Casual vs Formal).
   - Quan sát sự thay đổi trong `reason` (Giải thích) để đánh giá tính minh bạch.

---

## 📈 Trình bày kết quả (Reporting)

Dữ liệu thu được hỗ trợ việc thảo luận về:
- Tầm quan trọng của Context trong AI ra quyết định.
- Vai trò của Rule-based Decision Layer giúp tăng cường độ tin cậy cho Black-box Models (ResNet50).
- Cách tiếp cận XAI (Explainable AI) đơn giản nhưng hiệu quả trong việc xây dựng lòng tin với người dùng.
