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
