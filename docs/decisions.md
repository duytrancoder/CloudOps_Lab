# Báo cáo Quyết định Kiến trúc (Architecture Decision Records — ADR)

Tài liệu này ghi lại các quyết định kỹ thuật cốt lõi trong dự án CloudOps Lab, giải thích bối cảnh, các lựa chọn thay thế và lý do tại sao quyết định này là tối ưu nhất cho mục tiêu học tập và thực hành Cloud/DevOps thực chiến.

---

### ADR 001: Sử dụng Gunicorn làm WSGI Server thay cho Flask Development Server

* **Trạng thái**: Đã phê duyệt (Accepted)
* **Bối cảnh**: 
  Flask tích hợp sẵn lệnh `flask run` (hoặc `app.run()`), rất tiện lợi cho môi trường phát triển cục bộ. Tuy nhiên, server này là đơn luồng (single-threaded), không được tối ưu để xử lý tải đồng thời, và không xử lý tốt các tín hiệu hệ điều hành (`SIGTERM`, `SIGINT`) để dừng tiến trình an toàn (graceful shutdown).
* **Quyết định**: 
  Sử dụng **Gunicorn** làm WSGI HTTP server chạy ứng dụng Flask trong Docker container (ví dụ: `gunicorn --bind 0.0.0.0:8000 --workers 2 app.main:app`).
* **Lý do phù hợp với người học DevOps**:
  1. Giúp người học phân biệt rõ ràng giữa **Application Logic** (Flask) và **Process / Web Server Management** (Gunicorn).
  2. Hiểu cách cấu hình worker processes, worker timeouts và cơ chế nhận tín hiệu từ Docker/Linux khi container bị dừng hoặc khởi động lại.
  3. Đây là mô hình chuẩn mực trong môi trường sản xuất thực tế khi triển khai Python web apps.

---

### ADR 002: Tách biệt Liveness Probe (`/health/live`) và Readiness Probe (`/health/ready`)

* **Trạng thái**: Đã phê duyệt (Accepted)
* **Bối cảnh**: 
  Nhiều ứng dụng chỉ có một endpoint `/health` duy nhất. Khi triển khai bản phát hành mới hoặc khi ứng dụng đang khởi tạo tài nguyên, một endpoint duy nhất không thể phân biệt giữa:
  - Tiến trình đã chết hoàn toàn và cần được restart (Liveness).
  - Tiến trình vẫn sống nhưng chưa sẵn sàng nhận traffic người dùng (Readiness).
* **Quyết định**: 
  Triển khai 2 endpoints độc lập:
  - `/health/live`: Phản hồi nhanh (`200 OK`) chứng minh tiến trình web server đang chạy và không bị deadlock.
  - `/health/ready`: Kiểm tra điều kiện cần thiết để phục vụ request nghiệp vụ.
* **Lý do phù hợp với người học DevOps**:
  1. Hình thành tư duy thiết kế hệ thống chuẩn Cloud-native (tương thích hoàn toàn với Docker `HEALTHCHECK`, Kubernetes probes, hoặc AWS Target Group Health Checks sau này).
  2. Là mắt xích trọng yếu để xây dựng cơ chế **Tự động Rollback**: Script deploy sẽ liên tục thăm dò `/health/ready`, nếu không sẵn sàng trong một khoảng thời gian chờ (timeout) $\rightarrow$ lập tức khôi phục bản cũ.

---

### ADR 003: Sử dụng Docker Compose trên máy chủ đơn lẻ (Single VM)

* **Trạng thái**: Đã phê duyệt (Accepted)
* **Bối cảnh**: 
  Có 3 lựa chọn để chạy ứng dụng trên máy chủ:
  1. Chạy lệnh `docker run` thủ công với hàng loạt tham số flags.
  2. Dùng Docker Compose (`compose.yaml`).
  3. Dùng cụm điều phối container lớn như Kubernetes (K8s).
* **Quyết định**: 
  Sử dụng **Docker Compose** làm công cụ điều phối chính trên VM (sau khi đã thực hành `docker run` ở mức nền tảng ở Step 05).
* **Lý do phù hợp với người học DevOps**:
  1. **Tránh sai sót con người**: Toàn bộ cấu hình (port, environment, volume, healthcheck, restart policy) được khai báo thành mã nguồn (Declarative Configuration) trong `compose.yaml`, có thể version-control bằng Git.
  2. **Tránh phức tạp hóa quá sớm**: Kubernetes quá nặng và che giấu đi rất nhiều tương tác cốt lõi của Linux OS, networking và file permissions. Docker Compose cung cấp đủ sức mạnh để quản lý vòng đời container trên một máy chủ mà vẫn giữ hệ thống trong tầm kiểm soát.

---

### ADR 004: Cơ chế Tự động Rollback bằng Script Bash dựa trên Health Check

* **Trạng thái**: Đã phê duyệt (Accepted)
* **Bối cảnh**: 
  Khi tự động hóa triển khai bằng CI/CD, nếu bản phát hành mới có lỗi runtime (ví dụ lỗi syntax không bắt được bởi test, thiếu biến môi trường, crash khi nhận request thật), server sẽ rơi vào trạng thái ngừng hoạt động nếu không có cơ chế khôi phục.
* **Quyết định**: 
  Viết logic kiểm soát triển khai trong `scripts/deploy.sh`:
  1. Lưu lại image tag hiện tại (`PREVIOUS_TAG`).
  2. Cập nhật và khởi động image mới (`NEW_TAG`).
  3. Thăm dò (polling) `/health/ready` trong tối đa 30-60 giây.
  4. Nếu pass $\rightarrow$ ghi nhận thành công.
  5. Nếu timeout hoặc mã lỗi HTTP $\rightarrow$ tự động chạy lệnh rollback về `PREVIOUS_TAG` và exit code 1 để pipeline báo thất bại.
* **Lý do phù hợp với người học DevOps**:
  1. Giúp người học hiểu bản chất "bên dưới nắp ca-pô" (under the hood) của các hệ thống triển khai hiện đại (blue/green, canary, rolling update).
  2. Tạo ra kịch bản diễn tập thực chiến (Incident Drill) có thể kiểm chứng bằng mắt: cố tình deploy lỗi và thấy hệ thống tự cứu lấy chính mình.

---

### ADR 005: Chiến lược Giám sát phân tầng (Linux Native $\rightarrow$ Shell Script $\rightarrow$ AWS CloudWatch)

* **Trạng thái**: Đã phê duyệt (Accepted)
* **Bối cảnh**: 
  Có xu hướng cài đặt ngay các bộ công cụ giám sát đồ sộ như Prometheus, Grafana, Loki hoặc Datadog. Tuy nhiên, những công cụ này tiêu tốn nhiều RAM/CPU trên máy chủ nhỏ và làm người học phân tâm khỏi kỹ năng cốt lõi.
* **Quyết định**: 
  Chia việc giám sát thành 3 giai đoạn rõ rệt:
  1. **Tầng 1 (Cốt lõi)**: Làm chủ các lệnh Linux căn bản (`journalctl`, `docker compose logs`, `top/htop`, `df -h`, `free -h`, `ss -tulpn`).
  2. **Tầng 2 (Tự động hóa)**: Viết script `monitor.sh` kiểm tra ngưỡng dung lượng đĩa và trạng thái container.
  3. **Tầng 3 (Cloud)**: Tích hợp AWS CloudWatch Agent thu thập metrics và tạo Alarms trên hạ tầng AWS EC2.
* **Lý do phù hợp với người học DevOps**:
  1. Kỹ năng cứu nguy đầu tiên của một DevOps Engineer khi hệ thống giám sát chết chính là khả năng SSH vào server và dùng lệnh Linux để đọc log và chẩn đoán.
  2. Đi từ gốc rễ (hệ điều hành) lên ngọn (dịch vụ Cloud).
