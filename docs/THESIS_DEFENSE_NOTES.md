# 🎓 Ghi chú Bảo vệ Khóa luận (Thesis Defense Notes)

Dự án: **Outfit AI - Hệ thống Ra quyết định và Gợi ý trang phục dựa trên Ngữ cảnh**

---

## 1. Định vị Nghiên cứu (Research Positioning)

### Vấn đề Giải quyết (What we solve)
- Sự thiếu hụt tính logic và an toàn trong các hệ thống AI phân loại hình ảnh thuần túy.
- Khoảng cách giữa "nhận diện vật thể" (Object Detection) và "ra quyết định thực tế" (Actionable Decision Making).
- Tính minh bạch và khả năng giải thích của gợi ý (Explainability).

### Phạm vi loại trừ (What we DON'T solve)
- **Học máy thời gian thực**: Chúng tôi không huấn luyện lại model tại runtime; chúng tôi sử dụng model có sẵn phối hợp với tầng logic.
- **Thẩm mỹ cá nhân hóa phức tạp**: Hệ thống ưu tiên tính an toàn và tiện dụng hơn là các xu hướng thời trang thay đổi nhanh chóng.
- **Xử lý ảnh nhiễu cực đoan**: Hệ thống giả định ảnh đầu vào có độ rõ nét nhất định (đã được xử lý bởi rembg).

---

## 2. Tuyên bố về Đóng góp (Contribution Statement)

- **Đóng góp Khoa học**: Chứng minh hiệu quả của việc kết hợp "Rule-based Logic" và "Deep Learning" để tạo ra một hệ thống Hybrid AI có độ tin cậy cao hơn trong phối đồ.
- **Đóng góp Kỹ thuật**: Xây dựng tầng Decision Layer linh hoạt cho phép tách biệt dự đoán của model và quyết định nghiệp vụ (Decision vs Prediction).
- **Đóng góp Phương pháp luận**: Thiết lập một framework đánh giá cho phép so sánh định lượng giữa các chiến lược Baseline và Context-aware.

---

## 3. Các mối đe dọa đối với tính hợp lệ (Threats to Validity)

### Tính hợp lệ Nội bộ (Internal Validity)
- **Mối đe dọa**: Sự phụ thuộc vào chất lượng của API thời tiết bên ngoài.
- **Giảm thiểu**: Đã triển khai `context_override` cho phép chạy thực nghiệm trong điều kiện kiểm soát ổn định.

### Tính hợp lệ Bên ngoài (External Validity)
- **Mối đe dọa**: Tập dữ liệu huấn luyện model gốc có thể không bao phủ hết các loại trang phục vùng nhiệt đới/đặc thù địa phương.
- **Giảm thiểu**: Sử dụng taxonomy thời trang tổng quát hỗ trợ ánh xạ từ nhãn ImageNet sang các category phổ quát.

---

## 4. Chuẩn bị Câu hỏi Phản biện (Prepared Q&A)

**Q1: Tại sao không để AI tự học các quy tắc phối đồ thay vì sử dụng Decision Layer cố định?**
- *Trả lời*: Học máy thuần tùy yêu cầu tập dữ liệu nhãn khổng lồ và thường thiếu tính xác định (determinism). Trong nghiên cứu này, chúng tôi ưu tiên tính an toàn và khả năng giải thích—điều mà các quy tắc xác định cung cấp tốt hơn cho mục đích nghiên cứu nền tảng.

**Q2: Điều gì xảy ra nếu model phân loại sai (vd: phân loại áo khoác thành áo thun)?**
- *Trả lời*: Hệ thống sử dụng Confidence Threshold và Decision Status. Nếu độ tin cậy thấp, hệ thống sẽ đánh dấu `LOW_CONFIDENCE` và yêu cầu người dùng xác nhận, ngăn chặn việc ra quyết định dựa trên dữ liệu sai lệch.

**Q3: Hệ thống có khả năng mở rộng (scalability) như thế nào khi số lượng quy tắc tăng lên?**
- *Trả lời*: Kiến trúc dịch vụ hiện tại cho phép mở rộng `DecisionEngine` theo module. Tuy nhiên, chúng tôi thừa nhận rằng việc duy trì quá nhiều quy tắc thủ công sẽ phức tạp, đó là lý do tầng Decision Layer được thiết kế tối giản, tập trung vào các quy tắc an toàn cốt lõi.

**Q4: Yếu tố thời tiết thực tế có tác động thế nào đến độ chính xác của gợi ý?**
- *Trả lời*: Thực nghiệm cho thấy nhiệt độ là biến số quan trọng nhất. Hệ thống xử lý rung động dữ liệu thời tiết thông qua signature caching và làm tròn nhiệt độ để đảm bảo tính ổn định của gợi ý.

**Q5: Hạn chế lớn nhất của dự án này là gì?**
- *Trả lời*: Đó là tính tĩnh của các quy tắc. Thời trang là một lĩnh vực định tính và chủ quan. Dự án này tập trung vào khía cạnh "chức năng" (functional) hơn là khía cạnh "nghệ thuật" (stylistic).

---

## 5. Kết luận Bảo vệ
Hệ thống không cố gắng thay thế stylist con người, mà cung cấp một công cụ hỗ trợ dựa trên dữ liệu có tính đến các yếu tố an toàn và ngữ cảnh mà các ứng dụng AI cơ bản thường bỏ qua.
