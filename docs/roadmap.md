# Lộ trình Triển khai — 14 Steps CloudOps Lab

Lộ trình này chia nhỏ toàn bộ quá trình xây dựng, triển khai và vận hành hệ thống theo phương pháp tiếp cận từng bước có bằng chứng thực nghiệm (**Evidence-based Operations**).

---

## Phân cấp Cấp độ (Levels Overview)

* **Level 1 — Working Deployment (Bắt buộc)**: Bước 01 $\rightarrow$ Bước 05. Nắm vững Linux VM, Docker, non-root user, WSGI Gunicorn, health endpoints và triển khai thủ công an toàn.
* **Level 2 — Automated Operations (Mục tiêu cốt lõi)**: Bước 06 $\rightarrow$ Bước 11. Pipeline CI/CD tự động, GHCR versioning, script deploy + auto rollback có kiểm chứng, và điều tra sự cố qua công cụ Linux.
* **Level 3 — Cloud & Production Practices (Phần mở rộng)**: Bước 12 $\rightarrow$ Bước 14. Đưa lên AWS EC2, CloudWatch metrics/alarms, diễn tập sự cố (drills) và tài liệu portfolio hoàn chỉnh.

---

## Chi tiết Từng Bước (14 Steps)

### Level 1: Working Deployment (Bắt buộc)

#### Step 01: Project Setup & Requirements
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Thiết lập nền móng dự án, cấu trúc repository tinh gọn, tài liệu hóa kiến trúc và các quyết định kỹ thuật (ADRs).
* **Đầu vào**: Bối cảnh dự án, tech stack đã thống nhất.
* **Đầu ra**: Cấu trúc thư mục chuẩn, `.gitignore`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions.md`.
* **Tiêu chí nghiệm thu**: Mọi thành viên/người chấm đọc hiểu luồng phát hành; ranh giới công nghệ rõ ràng (không K8s, không DB thừa); git repository sạch sẽ.

#### Step 02: Build the Sample Application
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Xây dựng Flask web app tối giản có đầy đủ 2 health endpoints: `/health/live` và `/health/ready`.
* **Đầu vào**: Yêu cầu endpoint, cấu trúc project.
* **Đầu ra**: `app/main.py`, `app/config.py`, `tests/test_app.py`, cấu hình `ruff` và `pytest`.
* **Tiêu chí nghiệm thu**: Pytest pass 100% cho cả logic nghiệp vụ và response format của 2 health probes (`status: UP`, HTTP 200). Ruff check 0 lỗi.

#### Step 03: Dockerize the Application
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Đóng gói ứng dụng vào Docker image an toàn, dùng Gunicorn làm WSGI server và chạy dưới user không đặc quyền (`non-root`).
* **Đầu vào**: Ứng dụng Flask từ Step 02, requirements.
* **Đầu ra**: `Dockerfile`, `.dockerignore`, `compose.yaml` (cục bộ), Docker `HEALTHCHECK` directive.
* **Tiêu chí nghiệm thu**: Chạy container cục bộ, kiểm tra `whoami` trong container không phải `root`; `docker inspect` hiển thị trạng thái `healthy`; Gunicorn xử lý request ổn định.

#### Step 04: Linux & SSH Lab
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Chuẩn bị môi trường máy chủ Linux (Ubuntu VM cục bộ hoặc cloud instance) với chuẩn bảo mật cơ bản.
* **Đầu vào**: Máy chủ Ubuntu trắng.
* **Đầu ra**: Tạo deploy-user chuyên dụng, cấu hình SSH Key-based authentication (vô hiệu hóa SSH password), cài đặt Docker Engine & Docker Compose plugin, cấu hình Firewall (UFW: mở 22, 80/8000).
* **Tiêu chí nghiệm thu**: SSH vào server bằng key thành công mà không cần password; deploy-user chạy được Docker mà không cần quyền `root` toàn máy; ufw chặn các port không mong muốn.

#### Step 05: Deploy Manually
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Tự tay triển khai ứng dụng lên server Linux: ban đầu bằng lệnh `docker run`, sau đó chuyển sang `compose.yaml` để hiểu rõ sự khác biệt.
* **Đầu vào**: Docker image đã build, server Linux đã sẵn sàng từ Step 04.
* **Đầu ra**: File `compose.yaml` trên server, container chạy nền (`-d`).
* **Tiêu chí nghiệm thu**: Gọi `curl http://<SERVER_IP>:8000/health/ready` từ máy client trả về 200 OK; kiểm tra `docker compose ps` thấy trạng thái `Up (healthy)`.

---

### Level 2: Automated Operations (Mục tiêu cốt lõi)

#### Step 06: CI Pipeline
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Tự động hóa quy trình linting, testing và build container trên mỗi commit qua GitHub Actions.
* **Đầu vào**: Code base, tests, Dockerfile.
* **Đầu ra**: Workflow file `.github/workflows/ci.yml`.
* **Tiêu chí nghiệm thu**: Pull Request hoặc push commit kích hoạt workflow; tự động fail nếu vi phạm ruff hoặc pytest fail; build image thành công trên runner.

#### Step 07: Container Registry & Versioning
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Tự động push container image đã build lên GitHub Container Registry (GHCR) với cơ chế gắn tag chuẩn (Git SHA và Semantic version/latest).
* **Đầu vào**: Workflow CI từ Step 06, GitHub token / GHCR permissions.
* **Đầu ra**: Workflow CI được nâng cấp, image xuất hiện công khai/riêng tư trên GHCR của repo.
* **Tiêu chí nghiệm thu**: Image trên GHCR có thể được `docker pull` về máy bất kỳ; tag rõ ràng, có thể truy vết ngược về commit hash tương ứng.

#### Step 08: Automated Deployment
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Tự động hóa triển khai từ GitHub Actions tới server Linux qua SSH Key, cập nhật phiên bản mới không cần đăng nhập thủ công.
* **Đầu vào**: Image trên GHCR, SSH secrets trong GitHub Repo, server Linux.
* **Đầu ra**: Workflow file `.github/workflows/deploy.yml`, script triển khai `scripts/deploy.sh` trên host.
* **Tiêu chí nghiệm thu**: Push code mới lên `main` $\rightarrow$ CI pass $\rightarrow$ CD kích hoạt $\rightarrow$ Server tự pull image mới và khởi động lại container $\rightarrow$ Ứng dụng phản hồi phiên bản mới.

#### Step 09: Health Check & Rollback (Bằng chứng thực nghiệm)
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Xây dựng logic tự động rollback trong `deploy.sh` khi deployment phiên bản mới gặp lỗi readiness probe.
* **Đầu vào**: Script `scripts/deploy.sh`.
* **Đầu ra**: Cơ chế lưu `PREVIOUS_TAG`, logic polling check `/health/ready`, lệnh rollback tự động.
* **Tiêu chí nghiệm thu (Diễn tập thực tế)**:
  1. Triển khai bản v1.0.0 thành công.
  2. Cố tình deploy một commit v1.0.1 bị lỗi (ví dụ: làm endpoint `/health/ready` trả về HTTP 500 hoặc crash).
  3. Quan sát log: script phát hiện timeout/500, kích hoạt khôi phục về v1.0.0.
  4. Xác nhận server vẫn phục vụ bình thường bản v1.0.0, pipeline báo failed.

#### Step 10: Logging & Troubleshooting
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Làm chủ việc truy vết lỗi trên Linux qua logs container và hệ thống; viết tài liệu runbook ứng cứu.
* **Đầu vào**: Server đang chạy ứng dụng.
* **Đầu ra**: Hướng dẫn cấu hình log rotation trong Docker Compose (`max-size`, `max-file`), tài liệu `docs/runbooks/troubleshooting.md`.
* **Tiêu chí nghiệm thu**: Thực hành điều tra lỗi bằng `docker compose logs --tail=100 -f`, kết hợp `grep`, kiểm tra system logs qua `journalctl`.

#### Step 11: System Monitoring (Linux Native)
* **Phân loại**: Bắt buộc.
* **Mục tiêu**: Theo dõi sức khỏe tài nguyên hệ thống (CPU, RAM, Disk, Uptime) bằng các công cụ Linux bản địa và script kiểm tra định kỳ đơn giản.
* **Đầu vào**: Server Linux.
* **Đầu ra**: Script `scripts/monitor.sh` (kiểm tra disk threshold, memory, container status).
* **Tiêu chí nghiệm thu**: Script chạy phát hiện cảnh báo nếu dung lượng đĩa > 80% hoặc container down; xuất kết quả rõ ràng, có exit code phù hợp để tích hợp cron/alerting.

---

### Level 3: Cloud & Production-like Practices (Phần mở rộng)

#### Step 12: AWS & CloudWatch
* **Phân loại**: Mở rộng.
* **Mục tiêu**: Di chuyển ứng dụng lên AWS EC2, cấu hình IAM Role an toàn và cài đặt AWS CloudWatch Agent để thu thập metrics/logs lên Cloud.
* **Đầu vào**: Tài khoản AWS (Free Tier), EC2 Ubuntu.
* **Đầu ra**: EC2 instance chạy ứng dụng, cấu hình `amazon-cloudwatch-agent.json`.
* **Tiêu chí nghiệm thu**: Metrics CPU/Memory và logs container xuất hiện trên AWS CloudWatch Dashboard; cấu hình ít nhất 1 CloudWatch Alarm (ví dụ: CPU > 70% hoặc Health Check Fail).

#### Step 13: Incident Drills (Diễn tập sự cố thực chiến)
* **Phân loại**: Mở rộng.
* **Mục tiêu**: Thực hành các tình huống sự cố thực tế theo runbook: crashloop, đĩa đầy (disk exhaustion), và rò rỉ bộ nhớ (memory spike).
* **Đầu vào**: Kịch bản diễn tập, server đang chạy.
* **Đầu ra**: Tài liệu ghi nhận sự cố (Incident Post-mortem Report) trong `docs/runbooks/incident-reports/`.
* **Tiêu chí nghiệm thu**: Tái lập được sự cố $\rightarrow$ phát hiện qua monitoring/log $\rightarrow$ cô lập và xử lý theo runbook $\rightarrow$ phục hồi hệ thống $\rightarrow$ phân tích nguyên nhân gốc rễ (RCA).

#### Step 14: Documentation & Portfolio
* **Phân loại**: Mở rộng / Hoàn thiện.
* **Mục tiêu**: Đóng gói toàn bộ tài liệu dự án, sơ đồ, bằng chứng thực nghiệm (screenshots, log outputs) để phục vụ showcase năng lực DevOps.
* **Đầu vào**: Toàn bộ artifacts và kết quả qua 13 bước.
* **Đầu ra**: `README.md` hoàn chỉnh chuẩn portfolio tuyển dụng, video/GIF demo luồng CI/CD và Rollback.
* **Tiêu chí nghiệm thu**: Người khác có thể fork repository và tái lập toàn bộ lab từ con số 0 trong vòng 30 phút theo hướng dẫn.
