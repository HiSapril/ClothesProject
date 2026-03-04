# 📋 Báo cáo Thẩm định Chức năng (Validation Report)

Tài liệu này trình bày các kết quả thẩm định độ tin cậy và giới hạn hoạt động (operational boundaries) của hệ thống **Outfit AI**. Mục tiêu là trả lời câu hỏi: "Hệ thống hoạt động tin cậy trong phạm vi nào?"

---

## 1. Danh mục kịch bản kiểm tra (Test Scenarios)

Chúng tôi đã thực hiện 3 nhóm thử nghiệm tập trung vào các điểm biên của thuật toán:

| Nhóm thử nghiệm | Mục tiêu | Kết quả |
| :--- | :--- | :--- |
| **Biên nhiệt độ** | Kiểm tra sự chuyển đổi logic tại 18°C và 28°C. | **Pass**: Chuyển đổi mượt mà giữa các lớp trang phục. |
| **Độ bền tủ đồ** | Thử nghiệm khi thiếu hụt các danh mục thiết yếu. | **Handled**: Hệ thống trả về lỗi `INSUFFICIENT_WARDROBE` thay vì gợi ý sai. |
| **An toàn cực đoan** | Thử nghiệm tại nhiệt độ nguy hiểm (>45°C). | **Pass**: Decision Layer chặn hoàn toàn áo khoác dày. |

---

## 2. Xác định giới hạn hệ thống (System Boundaries)

Dựa trên thực nghiệm, hệ thống đạt độ tin cậy cao nhất trong các điều kiện sau:
- **Nhiệt độ**: từ -5°C đến 45°C. Ngoài phạm vi này, dữ liệu thời tiết có thể gây ra các phản ứng cực đoan trong scoring.
- **Tình trạng tủ đồ**: Yêu cầu tối thiểu 1 Top, 1 Bottom và 1 Footwear. Nếu thiếu, hệ thống sẽ rơi vào trạng thái "Degraded mode".
- **Độ tin cậy AI**: Chỉ các phân loại có Confidence > 50% mới được đưa vào logic phối đồ.

---

## 3. Phân tích các chế độ thất bại (Failure Modes)

Chúng tôi xác định hai loại thất bại chính:

### A. Thất bại An toàn (Safe Failure)
- **Kịch bản**: Người dùng tải ảnh nhiễu hoặc không phải quần áo.
- **Xử lý**: Decision Layer trả về `LOW_CONFIDENCE` kèm gợi ý hành động. 
- **Đánh giá**: Chấp nhận được trong nghiên cứu.

### B. Thất bại Thuật toán (Algorithmic Degradation)
- **Kịch bản**: Nhiệt độ tại ngưỡng 18°C.
- **Xử lý**: Hệ thống có thể dao động giữa việc "có áo khoác" hoặc "không áo khoác" tùy vào biến thiên nhỏ của dữ liệu.
- **Hành động**: Đã được xử lý bằng cách làm tròn nhiệt độ (rounding) để ổn định signature caching.

---

## 4. Tuyên bố về sự đảm bảo (System Guarantees)

Hệ thống **Outfit AI** cam kết:
1. **Không gợi ý trang phục gây nguy hiểm** (VD: áo khoác dày trong thời tiết cực nóng).
2. **Luôn cung cấp giải thích** cho mọi quyết định đầu ra.
3. **Minh bạch về các sai số của mô hình AI** thông qua việc hiển thị trạng thái Decision Status.

---

## 5. Kết luận (Conclusion)

Hệ thống chứng minh được tính vững chắc (robustness) trong các kịch bản biên. Mặc dù vẫn còn hạn chế ở tính đa dạng của quy tắc, nhưng các giới hạn an toàn được thiết lập đảm bảo rằng hệ thống không đưa ra các quyết định phi logic hoặc mất an toàn cho đối tượng nghiên cứu.
