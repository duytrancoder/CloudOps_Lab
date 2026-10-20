# CloudOps Lab — Automated Deployment, Monitoring & Incident Response

Hệ thống triển khai và vận hành ứng dụng Python trên Linux/Cloud, tự động hóa toàn diện quy trình CI/CD release, kiểm tra sức khỏe dịch vụ, giám sát tài nguyên và diễn tập ứng cứu sự cố thực chiến.

---

## 1. Tình huống Thực tế (Problem Statement)

Trong thực tế vận hành phần mềm, quy trình cập nhật thủ công (SSH vào server $\rightarrow$ kéo code $\rightarrow$ tự build $\rightarrow$ khởi động lại container) tiềm ẩn rủi ro rất lớn:
* Dễ nhầm lẫn phiên bản và cấu hình môi trường.
* Không có cơ chế xác minh xem ứng dụng có thực sự nhận request sau khi khởi động hay không.
* Khi bản phát hành bị lỗi (crash, sai config), không có cách khôi phục tức thời, gây downtime kéo dài.
* Thiếu khả năng quan sát (observability) về tài nguyên CPU, RAM, dung lượng đĩa và logs hệ thống.

**CloudOps Lab** giải quyết triệt để các vấn đề trên thông qua hệ thống tự động hóa khép kín:
1. Đóng gói ứng dụng chuẩn production bằng **Docker** (Gunicorn WSGI, non-root user).
2. Tự động hóa kiểm thử, linting và build image qua **GitHub Actions CI**.
3. Lưu trữ và đánh version bất biến trên **GitHub Container Registry (GHCR)**.
4. Tự động triển khai lên máy chủ **Linux VM / AWS EC2** qua **SSH Deployment Job**.
5. Xác thực dịch vụ sau release qua **Liveness/Readiness Probes** và **tự động Rollback** nếu gặp lỗi.
6. Giám sát hệ thống từ công cụ Linux bản địa đến **AWS CloudWatch**.

---

## 2. Kiến trúc Hệ thống

```text
[Developer] 
    │ git push
    ▼
[GitHub Actions CI] ──(Lint & Pytest)──► [Docker Build] ──► [GitHub Container Registry]
                                                                        │
                                                         SSH Trigger    │ Pull Image
                                                                        ▼
                                                             [Ubuntu Linux / AWS EC2]
                                                                │  Docker Compose
                                                                ▼
                                                          [App: Gunicorn + Flask]
                                                          ├── /health/live
                                                          └── /health/ready
                                                                │
                                                Verification & Auto-Rollback
                                                                │
                                                   [Monitoring & Diagnostics]
                                                   (Linux CLI / Script / CloudWatch)
```

> Xem tài liệu chi tiết tại: [docs/architecture.md](docs/architecture.md)

---

## 3. Công nghệ Cốt lõi (Tech Stack)

| Hạng mục | Công nghệ | Mục đích sử dụng |
| :--- | :--- | :--- |
| **Application** | Python 3.11+, Flask | Dịch vụ web mẫu và các endpoint probes |
| **WSGI Server** | Gunicorn | Server quản lý worker, concurrency và graceful shutdown |
| **Quality & Tests** | Ruff, pytest | Kiểm tra cú pháp nhanh và kiểm thử tự động hành vi app |
| **Containerization** | Docker, Compose | Đóng gói an toàn (non-root), quản lý khai báo dịch vụ |
| **CI/CD** | GitHub Actions | Tự động hóa pipeline Lint $\rightarrow$ Test $\rightarrow$ Build $\rightarrow$ Deploy |
| **Registry** | GitHub Container Registry | Lưu trữ image theo Git SHA và phiên bản phát hành |
| **Host System** | Ubuntu Linux VM / AWS EC2 | Môi trường máy chủ chạy ứng dụng thực tế |
| **Observability** | Linux CLI, Bash, CloudWatch | Giám sát tài nguyên, phân tích log và cảnh báo sự cố |

---

## 4. Cấu trúc Repository

```text
CloudOps_Lab/
├── .github/
│   └── workflows/          # CI/CD Workflows (CI check, GHCR publish, SSH Deploy)
├── app/
│   ├── __init__.py
│   ├── main.py             # Ứng dụng Flask & Health endpoints
│   └── config.py           # Cấu hình nạp từ biến môi trường
├── tests/
│   ├── __init__.py
│   └── test_app.py         # Kiểm thử đơn vị & kiểm thử health probes
├── scripts/
│   ├── deploy.sh           # Script triển khai & tự động rollback trên server
│   └── monitor.sh          # Script kiểm tra tài nguyên & sức khỏe hệ thống
├── docs/
│   ├── architecture.md     # Tài liệu kiến trúc & ranh giới phạm vi
│   ├── roadmap.md          # Chi tiết 14 bước thực hiện & tiêu chí nghiệm thu
│   ├── decisions.md        # Báo cáo quyết định kiến trúc (ADRs)
│   └── runbooks/           # Hướng dẫn ứng cứu & điều tra sự cố thực tế
├── compose.yaml            # Khai báo dịch vụ Docker Compose trên máy chủ
├── Dockerfile              # Chỉ dẫn build container an toàn (non-root user)
├── .dockerignore           # Danh sách loại trừ khi build Docker image
├── .gitignore              # Danh sách loại trừ khi commit Git
├── requirements.txt        # Thư viện runtime (Flask, Gunicorn)
└── requirements-dev.txt    # Thư viện phục vụ dev & test (pytest, ruff)
```

---

## 5. Lộ trình Thực hiện (14 Steps)

Dự án được chia thành 3 cấp độ rõ ràng:
* **Level 1 — Working Deployment (Bắt buộc)**: Bước 01 $\rightarrow$ Bước 05.
* **Level 2 — Automated Operations (Mục tiêu cốt lõi)**: Bước 06 $\rightarrow$ Bước 11.
* **Level 3 — Cloud & Production Practices (Phần mở rộng)**: Bước 12 $\rightarrow$ Bước 14.

> Chi tiết mục tiêu, đầu vào, đầu ra và tiêu chí nghiệm thu từng bước xem tại: [docs/roadmap.md](docs/roadmap.md)

---

## 6. Quyết định Kỹ thuật (Architecture Decision Records)

Tất cả các lựa chọn công nghệ đều bám sát triết lý: **tối ưu cho người học DevOps, hiểu sâu bản chất, kiểm chứng bằng thực tế, không dùng công cụ quá khổ**.
* **ADR 001**: Gunicorn thay vì `flask run` (quản lý tiến trình chuẩn production).
* **ADR 002**: Tách biệt Liveness `/health/live` và Readiness `/health/ready`.
* **ADR 003**: Dùng Docker Compose trên VM thay vì Kubernetes.
* **ADR 004**: Tự động Rollback bằng Bash Script có polling probe.
* **ADR 005**: Giám sát phân tầng (Linux Native $\rightarrow$ Script $\rightarrow$ AWS CloudWatch).

> Chi tiết bối cảnh và lý do chọn lựa xem tại: [docs/decisions.md](docs/decisions.md)

---

## 7. Nguyên tắc Bảo mật (Security & Safety)

* **Không commit Secrets/Credentials**: Tuyệt đối không lưu file `.env`, SSH Private Key, AWS Access Key hoặc Access Token vào Git repository.
* **Non-root Container**: Container được cấu hình chạy dưới user thông thường (`appuser`), hạn chế tối đa nguy cơ container escape.
* **SSH Hardening**: Đăng nhập máy chủ chỉ sử dụng SSH Key-pair, vô hiệu hóa mật khẩu (`PasswordAuthentication no`).

---

## 8. Hướng dẫn Phát triển & Kiểm thử Cục bộ (Local Development & Testing)

### 8.1. Khởi tạo Môi trường Ảo & Cài đặt Dependencies

```bash
# 1. Tạo virtual environment
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Cài đặt dependencies (bao gồm dev & test tools)
pip install -r requirements-dev.txt
```

### 8.2. Chạy Ứng dụng

* **Chế độ Phát triển (Development Mode)**:
  ```bash
  python3 -m app.main
  # hoặc dùng Flask CLI:
  FLASK_APP=app.main:app flask run --port 8000
  ```

* **Chế độ Production-like với WSGI Gunicorn (ADR 001)**:
  ```bash
  gunicorn --bind 0.0.0.0:8000 --workers 2 app.main:app
  ```

### 8.3. Danh sách Endpoints & Ý nghĩa Vận hành

| Phương thức | Endpoint | Ý nghĩa vận hành & Probe Type | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Trả về thông tin metadata dịch vụ, phiên bản và trạng thái | `200 OK` |
| `GET` | `/health/live` | **Liveness probe**: Kiểm tra tiến trình web server còn sống, không deadlock | `200 OK` |
| `GET` | `/health/ready` | **Readiness probe**: Kiểm tra dịch vụ sẵn sàng đón nhận request (dùng cho Rollback trigger) | `200 OK` |
| `GET` | `/health` | **Composite probe**: Báo cáo tổng hợp sức khỏe (kết hợp cả liveness & readiness) | `200 OK` |

### 8.4. Chạy Kiểm thử & Kiểm tra Chất lượng Code

* **Chạy toàn bộ Pytest test suite**:
  ```bash
  pytest
  ```

* **Kiểm tra cú pháp & chuẩn format với Ruff**:
  ```bash
  ruff check app tests
  ```

---

## 9. Đóng gói & Chạy Container Cục bộ (Docker Local Run — Step 03)

### 9.1. Build Docker Image

```bash
docker build -t cloudops-lab:step-03 .
```

### 9.2. Khởi chạy Container (với Non-root User & Gunicorn)

```bash
docker run -d \
  --name cloudops-lab-app \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e APP_VERSION=1.0.0 \
  cloudops-lab:step-03
```

### 9.3. Kiểm tra Trạng thái Sức khỏe & Xác thực Non-root

* **Kiểm tra trạng thái Container & Healthcheck**:
  ```bash
  docker ps --filter "name=cloudops-lab-app"
  # Xem chi tiết log của health probe:
  docker inspect --format '{{json .State.Health}}' cloudops-lab-app | jq .
  ```

* **Xác thực User thực tế bên trong container (Bảo mật Non-root)**:
  ```bash
  docker exec cloudops-lab-app id
  # Kết quả mong đợi: uid=1001(appuser) gid=1001(appuser) groups=1001(appuser)
  ```

* **Xem Logs hệ thống**:
  ```bash
  docker logs -f cloudops-lab-app
  ```

### 9.4. Dừng và Dọn dẹp Container

```bash
# Dừng container an toàn (Gunicorn đón nhận SIGTERM để graceful shutdown)
docker stop cloudops-lab-app

# Xóa container sau khi kiểm thử
docker rm cloudops-lab-app
```

---

## 10. Quản trị Linux & Truy cập SSH An toàn (Step 04 — Local Lab)

### 10.1. Cặp Khóa Riêng & Định danh Tài khoản
* Khóa SSH riêng của Lab: `~/.ssh/id_ed25519_cloudops` (cô lập 100% với khóa GitHub).
* Tài khoản vận hành: `deployer` (UID/GID 1001, không có quyền sudo, không thuộc nhóm docker).
* Cơ chế cô lập: `deployer` bị chặn hoàn toàn khi truy cập thư mục người dùng khác (`Permission denied`).

### 10.2. Lệnh Kết nối SSH Kiểm chứng

```bash
# Kết nối an toàn chỉ định duy nhất khóa lab
ssh -i ~/.ssh/id_ed25519_cloudops -o IdentitiesOnly=yes deployer@127.0.0.1
```

> Chi tiết runbook chẩn đoán mạng, rủi ro bind cổng và hướng dẫn khắc phục xem tại: [docs/runbooks/ssh-access.md](docs/runbooks/ssh-access.md)

---

## 11. Triển khai Thủ công bằng Docker Compose (Step 05 — Local Deployment)

### 11.1. Lệnh Khởi động Dịch vụ

```bash
# Xác thực cấu hình và build/chạy ứng dụng
docker compose config
docker compose up -d --build
```

### 11.2. Kiểm tra Vận hành & Sức khỏe Dịch vụ

```bash
# Kiểm tra trạng thái container và cổng bind (127.0.0.1:8000)
docker compose ps
ss -tlnp | grep :8000

# Gọi các probes kiểm chứng
curl -s -i http://127.0.0.1:8000/health
curl -s -i http://127.0.0.1:8000/health/ready

# Xem logs container
docker compose logs --tail=100 app
```

### 11.3. Quản lý Vòng đời & Dọn dẹp

```bash
# Tạm dừng và tiếp tục
docker compose stop app
docker compose start app

# Dọn dẹp dịch vụ
docker compose down
```

> Chi tiết phân biệt các lệnh vòng đời container (`stop`, `start`, `restart`, `up -d --build`, `down`) và 2 kịch bản xử lý sự cố (xung đột cổng, lỗi schema) xem tại: [docs/runbooks/manual-deployment.md](docs/runbooks/manual-deployment.md)




