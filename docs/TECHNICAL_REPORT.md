# 📄 Báo cáo Công nghệ: Hệ thống Gợi ý Trang phục Dựa trên Ngữ cảnh (Outfit AI)

## 1. Kiến trúc Hệ thống Tổng thể (Overall System Architecture)

Hệ thống được thiết kế theo kiến trúc phân tầng (Layered Architecture) nhằm đảm bảo tính module hóa và tách biệt các mối quan tâm (Separation of Concerns). Kiến trúc này cho phép nghiên cứu độc lập từng thành phần từ suy luận AI đến logic ra quyết định.

- **Tầng API (API Layer)**: Xây dựng trên FastAPI, chịu trách nhiệm nhận yêu cầu, xác thực người dùng và điều phối các tác vụ bất đồng bộ.
- **Tầng Suy luận AI (AI Inference Layer)**: Sử dụng Celery làm worker để xử lý các mô hình học sâu (ResNet50) một cách bất đồng bộ, tránh làm nghẽn luồng xử lý chính.
- **Tầng Quyết định (Decision Layer)**: Đây là thành phần cốt lõi của nghiên cứu, nơi các kết quả thô từ AI được lọc và xử lý thông qua các quy tắc nghiệp vụ xác định (Deterministic Rules).
- **Tầng Dữ liệu & Lưu trữ (Data & Storage Layer)**: Kết hợp PostgreSQL cho dữ liệu quan hệ và Redis cho quản lý hàng đợi và bộ nhớ đệm (Caching).

**Lý do lựa chọn**: Kiến trúc module giúp dễ dàng thay thế mô hình AI hoặc thay đổi quy tắc quyết định mà không ảnh hưởng đến toàn bộ hệ thống, điều này cực kỳ quan trọng trong thực nghiệm khoa học.

---

## 2. Nền tảng Công nghệ Backend (Backend Technology Stack)

- **Ngôn ngữ & Framework**: Python 3.x và FastAPI. FastAPI được chọn vì hiệu năng cao (hiệu năng tiệm cận Go/Node.js) và khả năng hỗ trợ kiểu dữ liệu (typing) mạnh mẽ, giúp giảm thiểu sai sót trong lập trình.
- **Thiết kế API**: Tuân thủ phong cách RESTful, đảm bảo tính nhất quán và dễ dàng tích hợp với các hệ thống khác.
- **Xác thực (Authentication)**: Sử dụng JWT (JSON Web Tokens) với cơ chế Access/Refresh token để đảm bảo an ninh dữ liệu nghiên cứu của người dùng.
- **Xử lý tác vụ nền**: Celery phối hợp với Redis làm Broker. Đây là lựa chọn tiêu chuẩn trong các hệ thống xử lý AI để quản lý tài nguyên tính toán hiệu quả.

---

## 3. Quy trình Trí tuệ Nhân tạo & Học máy (AI & Machine Learning Pipeline)

- **Kiến trúc Mô hình**: Sử dụng ResNet50 (Residual Network) được huấn luyện trước trên tập dữ liệu ImageNet thông qua kỹ thuật Transfer Learning để phân loại trang phục.
- **Tiền xử lý dữ liệu**:
  - Loại bỏ phông nền bằng thư viện `rembg` để giảm nhiễu và tập trung vào đặc trưng vật thể.
  - Chuẩn hóa kích thước ảnh (Resizing) về 224x224 pixel để phù hợp với input của mô hình.
- **Quy trình suy luận**: Ảnh sau khi tiền xử lý được đưa qua mô hình để lấy xác suất lớp (class probabilities).
- **Ngưỡng tin cậy (Confidence Thresholds)**: Hệ thống áp dụng các ngưỡng động để phân loại kết quả thành `CONFIRMED` (>85%) hoặc `LOW_CONFIDENCE` (50-85%).

**Phân tích Thực nghiệm: Vai trò của Việc tách nền (Background Removal)**:
Trong các nghiên cứu về Thị giác máy tính (Computer Vision), việc tách nền đóng vai trò là một bộ lọc "Tăng tỷ lệ Tín hiệu trên Nhiễu" (Signal-to-Noise Ratio). 
1. **Lợi ích**: Giúp mô hình tập trung hoàn toàn vào các đặc trưng của vật phẩm (vải, form dáng, màu sắc) mà không bị ảnh hưởng bởi môi trường xung quanh (phòng ngủ, móc treo). Điều này giúp ổn định hóa accuracy khi triển khai thực tế.
2. **Rủi ro (Over-segmentation)**: Nếu thuật toán tách nền (rembg) bị lỗi và lược bỏ các bộ phận quan trọng (như ống tay áo), mô hình AI có thể bị đánh lừa (ví dụ: nhầm Long-sleeve thành T-shirt). 
3. **Giải pháp trong Outfit AI**: Tầng Quyết định (Decision Layer) sẽ bắt được các trường hợp này thông qua chỉ số Confidence thấp, từ đó yêu cầu người dùng xác nhận lại hoặc chụp lại ảnh.

**Lưu ý**: Mô hình AI chỉ đóng vai trò phân loại (classifier). Việc ra quyết định cuối cùng được chuyển sang tầng Decision Layer để đảm bảo tính an toàn và minh bạch.

---

## 4. Thiết kế Trí tuệ Gợi ý (Recommendation Intelligence Design)

Hệ thống so sánh hai chiến lược chính:
- **Chiến lược BASELINE**: Quy tắc đơn giản là chọn ngẫu nhiên các danh mục quần áo hợp lệ (Áo + Quần + Giày).
- **Chiến lược CONTEXT_AWARE**: Tích hợp dữ liệu thời tiết (Nhiệt độ, Điều kiện), Sự kiện (Casual, Formal, Sport) và quy mô tủ đồ cá nhân.
- **Động lực Khoa học (Hybrid AI)**: Kết hợp Học máy (ML) cho khả năng nhận diện thị giác và Quy tắc xác định (Deterministic Rules) cho khả năng suy luận logic. Cách tiếp cận này giúp khắc phục nhược điểm "hộp đen" của AI truyền thống.

---

## 5. Tầng Quyết định & Chốt chặn An toàn (Decision Layer)

Tầng Decision Layer hoạt động như một bộ lọc an toàn:
- **Phân loại Trạng thái & Lỗi**: Sử dụng `ClassificationStatus` và `FailureCode` (như `LOW_CONFIDENCE`, `INSUFFICIENT_WARDROBE`) để cung cấp phản hồi rõ ràng.
- **Quy tắc An toàn**: Ngăn chặn các gợi ý phi logic như mặc áo khoác dày khi nhiệt độ trên 35°C hoặc phối đồ thể thao cho sự kiện trang trọng.
- **Khả năng giải thích (XAI-lite)**: Mỗi gợi ý đều đi kèm một lời giải thích deterministic dựa trên các tham số đầu vào, giúp người dùng hiểu rõ "tại sao" AI lại đưa ra kết quả đó.

---

## 6. Hỗ trợ Dữ liệu & Đánh giá (Data & Evaluation Support)

- **Dataset**: Sử dụng các tập dữ liệu mẫu (`sample_labels.json`) làm ground truth để đánh giá độ chính xác của phân loại.
- **Tập lệnh đánh giá nghiên cứu**: `evaluate_ai.py` và `research_eval.py` được phát triển để đo lường định lượng các chỉ số như độ chính xác (Accuracy), tỷ lệ vi phạm an toàn (Safety Violation Rate), và chất lượng gợi ý.
- **Mô phỏng kịch bản**: Chức năng `context_override` cho phép các nhà nghiên cứu tạo ra các tình huống giả định (vd: đợt nắng nóng hoặc lạnh giá) một cách chủ động.

---

## 7. Cơ sở Hạ tầng & Tính tái lập (Infrastructure & Reproducibility)

- **Docker & Docker Compose**: Toàn bộ hệ thống được container hóa. Điều này đảm bảo môi trường thực nghiệm là nhất quán hoàn toàn giữa các máy tính khác nhau.
- **Cách ly dịch vụ**: Mỗi thành phần (DB, Redis, API, Worker) chạy trong một container riêng biệt, phản ánh đúng cấu trúc của một hệ thống cloud-native hiện đại.
- **Tính tái lập**: Việc sử dụng Docker kết hợp với snapshot database đảm bảo rằng các thí nghiệm có thể được lặp lại với kết quả giống hệt nhau.

---

## 8. Hạn chế của Hệ thống (System Limitations)

- **Quy tắc dựa trên logic (Rule-based)**: Hệ thống phụ thuộc vào tính đúng đắn của các quy tắc do con người thiết lập, có thể chưa bao phủ hết tính thẩm mỹ đa dạng.
- **Kích thước dữ liệu**: Thử nghiệm hiện tại dựa trên quy mô nhỏ, cần tập dữ liệu lớn hơn để đánh giá khả năng mở rộng.
- **Phụ thuộc ngoại vi**: Việc gợi ý phụ thuộc lớn vào độ chính xác của API thời tiết bên ngoài và dữ liệu Google Calendar.

---

## 9. Tóm tắt Kỹ thuật (Summary)

Dự án **Outfit AI** không chỉ là một ứng dụng phần mềm đơn thuần mà là một nền tảng thực nghiệm khoa học. Sự kết hợp giữa **Machine Learning** cho thị giác máy tính và **Deterministic Logic** cho việc ra quyết định đã tạo ra một hệ thống hybrid có độ tin cậy cao, khả năng giải thích rõ ràng và dễ dàng thẩm định. Đây là một minh chứng kỹ thuật vững chắc cho việc ứng dụng AI có kiểm soát trong đời sống thực tế.
