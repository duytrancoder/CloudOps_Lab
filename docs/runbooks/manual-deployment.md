# Sổ tay Triển khai Thủ công bằng Docker Compose (Manual Deployment Runbook) — Step 05

Tài liệu hướng dẫn quy trình triển khai, kiểm tra sức khỏe, quản lý vòng đời container và chẩn đoán sự cố cho ứng dụng **CloudOps Lab** trên máy chủ Linux đơn lẻ.

---

## 1. Bối cảnh & Ranh giới Kỹ thuật (Scope Notice)

> [!NOTE]
> Đây là bài thực hành **Local Deployment** trên hệ điều hành Arch Linux sử dụng Docker Compose v2.
> Cổng dịch vụ được cấu hình ràng buộc nghiêm ngặt vào loopback `127.0.0.1:8000` để đảm bảo an toàn, tránh phơi bày ứng dụng ra mạng Wi-Fi LAN cá nhân.

---

## 2. Kiến trúc & Luồng Xử lý Yêu cầu (Request Flow)

```text
[Client / Curl trên Host]
         │ (HTTP GET http://127.0.0.1:8000)
         ▼
[Host Loopback Interface (127.0.0.1:8000)]
         │ Docker Port Forwarding (NAT)
         ▼
[Docker Bridge Network (cloudops_lab_default)]
         │
         ▼
[Container: cloudops_lab-app-1 (Port 8000)]
    ├── Gunicorn Master Process (PID 1, non-root appuser: 1001)
    │     ├── Worker Process 1 (PID 7)
    │     └── Worker Process 2 (PID 8)
    └── Flask Application (app.main:app)
          ├── GET /                -> 200 OK (Metadata & Version)
          ├── GET /health/live     -> 200 OK (Liveness Probe)
          ├── GET /health/ready    -> 200 OK (Readiness Probe)
          └── GET /health          -> 200 OK (Composite Report)
```

---

## 3. Điều kiện Tiên quyết (Prerequisites)

* Hệ điều hành: Linux (Arch Linux, Ubuntu hoặc tương đương).
* Docker Engine đã cài đặt và daemon đang hoạt động (`docker version`).
* Docker Compose v2 plugin (`docker compose version >= 2.0`).
* Cổng `8000` trên host chưa bị tiến trình nào chiếm dụng (`ss -tlnp | grep :8000`).

---

## 4. Cấu hình Dịch vụ (`compose.yaml`)

File khai báo tối giản, không phụ thuộc file `.env` ngoài luồng:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: cloudops-lab:step-05
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - APP_NAME=CloudOps Lab App
      - APP_VERSION=1.0.0
      - APP_ENV=production
      - LOG_LEVEL=INFO
      - PORT=8000
    restart: unless-stopped
```

* **`ports: ["127.0.0.1:8000:8000"]`**: Chỉ bind vào loopback, cô lập tuyệt đối khỏi mạng ngoài.
* **`restart: unless-stopped`**: Tự động hồi sinh container nếu app gặp lỗi crash hoặc khi Docker daemon khởi động lại, nhưng sẽ tôn trọng quyết định dừng chủ động của kỹ sư vận hành.

---

## 5. Quy trình Vận hành Chuẩn (Standard Operating Procedures)

### 5.1. Triển khai Ứng dụng (Deploy)

```bash
# 1. Kiểm tra tính hợp lệ của cấu hình
docker compose config

# 2. Build image và khởi chạy container nền
docker compose up -d --build
```

### 5.2. Kiểm tra Trạng thái & Sức khỏe (Verify)

```bash
# 1. Kiểm tra trạng thái container và healthcheck
docker compose ps
# Kết quả mong đợi: Status hiển thị "Up ... (healthy)"

# 2. Xác minh cổng lắng nghe trên host
ss -tlnp | grep :8000
# Kết quả mong đợi: LISTEN trên 127.0.0.1:8000

# 3. Xác minh định danh non-root bên trong container
docker compose exec app id
# Kết quả mong đợi: uid=1001(appuser) gid=1001(appuser)

# 4. Kiểm tra phản hồi HTTP từ các endpoints
curl -s -i http://127.0.0.1:8000/
curl -s -i http://127.0.0.1:8000/health/live
curl -s -i http://127.0.0.1:8000/health/ready
curl -s -i http://127.0.0.1:8000/health
```

### 5.3. Xem Logs Vận hành

```bash
# Xem 100 dòng log gần nhất
docker compose logs --tail=100 app

# Theo dõi log thời gian thực
docker compose logs -f app
```

---

## 6. Phân biệt các Lệnh Quản lý Vòng đời Container (Lifecycle)

Trong vận hành thực tế, cần phân biệt chính xác tác động của từng lệnh:

| Lệnh | Trạng thái Container | Trạng thái Network & File | Trường hợp Sử dụng |
| :--- | :--- | :--- | :--- |
| **`docker compose stop`** | Tiến trình dừng (`Exited (0)`), container vẫn tồn tại | Giữ nguyên toàn bộ filesystem của container và network bridge | Tạm dừng dịch vụ để bảo trì hoặc kiểm tra khi app down. |
| **`docker compose start`** | Khởi động lại container đang bị dừng | Giữ nguyên container ID và dữ liệu đã có | Tiếp tục chạy lại dịch vụ sau khi bảo trì. |
| **`docker compose restart`** | Gửi tín hiệu dừng rồi khởi động lại ngay | Giữ nguyên container ID, **KHÔNG** rebuild image, **KHÔNG** nạp lại biến môi trường mới | Khởi động lại nhanh app khi bị nghẽn luồng hoặc rò rỉ RAM tạm thời. |
| **`docker compose up -d --build`** | Tạo mới hoặc recreate container nếu có thay đổi | Rebuild image mới, recreate container mới thay thế container cũ | Triển khai phiên bản code mới hoặc áp dụng thay đổi cấu hình `compose.yaml`. |
| **`docker compose down`** | Dừng và **XÓA HOÀN TOÀN** container | Xóa network bridge nội bộ; volume giữ nguyên (trừ khi thêm cờ `-v`) | Dọn dẹp sạch sẽ tài nguyên sau khi kết thúc đợt lab. |

---

## 7. Sổ tay Xử lý Sự cố Thực tế (Troubleshooting Runbook)

### Sự cố 1: Xung đột Cổng Host (`Port is already allocated`)

* **Triệu chứng thực tế**:
  Khi chạy `docker compose up -d`, daemon báo lỗi:
  ```text
  Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint ...: Bind for 127.0.0.1:8000 failed: port is already allocated
  ```
* **Lệnh chẩn đoán**:
  ```bash
  # Tìm tiến trình đang chiếm cổng 8000
  ss -tlnp | grep :8000
  # Hoặc kiểm tra container nào đang giữ cổng
  docker ps --filter "publish=8000"
  ```
* **Nguyên nhân**: Đã có một tiến trình web server hoặc một container khác đang lắng nghe trên cổng `8000`.
* **Cách khắc phục**:
  1. Xác định tiến trình/container đang chiếm dụng cổng.
  2. Nếu là container cũ của bài lab trước: chạy `docker compose down` trên project đó.
  3. Nếu cổng 8000 thuộc dịch vụ khác bắt buộc chạy: đổi cổng host trong `compose.yaml` (ví dụ `127.0.0.1:8080:8000`), giữ nguyên cổng container 8000.
* **Xác minh sau khắc phục**:
  Chạy lại `docker compose up -d` và kiểm tra `docker compose ps` báo `Up (healthy)`.

---

### Sự cố 2: Lỗi Cú pháp Cấu hình Compose (`Schema Validation Error`)

* **Triệu chứng thực tế**:
  Khi chạy `docker compose config` hoặc `up`, Compose báo lỗi:
  ```text
  validating compose.yaml: services.app.port_mappings false schema
  ```
* **Lệnh chẩn đoán**:
  ```bash
  docker compose config
  ```
* **Nguyên nhân**: Trường cấu hình bị sai chính tả (ví dụ gõ `port_mappings:` thay vì `ports:`), hoặc lỗi thụt lề YAML sai quy định.
* **Cách khắc phục**:
  1. Đọc kỹ đường dẫn lỗi được chỉ định (ở đây là `services.app.port_mappings`).
  2. Tra cứu chuẩn Compose Specification và sửa lại đúng tên trường: `ports:`.
* **Xác minh sau khắc phục**:
  Chạy `docker compose config`. Lệnh phải trả về mã thoát 0 và in ra cấu hình chuẩn hóa mà không kèm theo thông báo lỗi schema.
