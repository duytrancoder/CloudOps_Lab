# Sổ tay Vận hành & Truy cập SSH (SSH Access Runbook) — Step 04

Tài liệu hướng dẫn quy trình xác thực SSH an toàn, quản lý tài khoản vận hành, chẩn đoán cổng mạng và kiểm soát rủi ro bảo mật trên máy chủ Arch Linux.

---

## 1. Bối cảnh & Ranh giới Thực nghiệm (Scope Notice)

> [!NOTE]
> Bài thực hành này là **Local SSH Lab** được thực hiện trực tiếp trên hệ điều hành Arch Linux. Client và SSH Server cùng nằm trên một máy chủ (kết nối qua loopback `127.0.0.1`).
> Kết quả kiểm chứng chứng minh cơ chế xác thực Public-key, phân quyền người dùng và cô lập tài khoản Linux; không đại diện cho việc triển khai qua mạng vật lý độc lập.

---

## 2. Thông tin Cặp Key & Cơ chế Xác thực

Để bảo vệ an toàn tối đa cho máy tính cá nhân, dự án áp dụng nguyên tắc **"Khóa riêng cho từng mục đích"**:
* **Key GitHub hiện có**: `~/.ssh/id_ed25519` (Giữ nguyên vẹn, không dùng chung cho lab).
* **Key riêng của CloudOps Lab**:
  * Private key: `~/.ssh/id_ed25519_cloudops` (Quyền: `600`, không bao giờ commit vào Git).
  * Public key: `~/.ssh/id_ed25519_cloudops.pub` (Quyền: `644`).
  * Fingerprint: `256 SHA256:mGO/MjL0Wh5LqpNzEmIQI1Ngu/ePleZrZJqD4pFDqJE cloudops-lab-deployer (ED25519)`.

---

## 3. Thiết lập Tài khoản `deployer` & Nguyên tắc Cô lập (User Isolation)

Tài khoản `deployer` được tạo ra chuyên phục vụ tự động hóa và vận hành, tuân thủ nguyên tắc đặc quyền tối thiểu (**Principle of Least Privilege**):

| Thuộc tính | Giá trị Thực tế | Ý nghĩa Bảo mật |
| :--- | :--- | :--- |
| **UID / GID** | `1001:1001` | Tài khoản hệ thống thông thường |
| **Nhóm (Groups)** | `1001(deployer)` | **Tuyệt đối KHÔNG thuộc nhóm `wheel`, `sudo` hay `docker`** |
| **Thư mục Home** | `/home/deployer` | Quyền `700` (`drwx------ deployer deployer`) |
| **Thư mục SSH** | `/home/deployer/.ssh` | Quyền `700` (`drwx------ deployer deployer`) |
| **File Authorized Keys** | `/home/deployer/.ssh/authorized_keys` | Quyền `600` (`-rw------- deployer deployer`) |

### Bằng chứng Cô lập Người dùng (Evidence of Isolation)
Khi đăng nhập với tư cách `deployer`, người dùng hoàn toàn bị chặn khi cố gắng đọc dữ liệu cá nhân của user `khxnhduy`:
```bash
[deployer@archlinux ~]$ ls /home/khxnhduy
ls: cannot open directory '/home/khxnhduy': Permission denied
```

---

## 4. Hướng dẫn Kết nối & Chẩn đoán

### 4.1. Lệnh Kết nối Chuẩn

```bash
ssh -i ~/.ssh/id_ed25519_cloudops -o IdentitiesOnly=yes deployer@127.0.0.1
```

* **Ý nghĩa các tham số**:
  * `-i ~/.ssh/id_ed25519_cloudops`: Chỉ định chính xác file private key dành riêng cho lab.
  * `-o IdentitiesOnly=yes`: **Rất quan trọng**. Bắt buộc SSH client chỉ sử dụng duy nhất key được truyền qua cờ `-i`, ngăn chặn client âm thầm thử các key khác trong `ssh-agent` hoặc key GitHub.

### 4.2. Lệnh Kiểm tra Nhanh trên Máy

```bash
# Kiểm tra phiên làm việc và định danh
whoami    # Output mong đợi: deployer
id        # Output mong đợi: uid=1001(deployer) gid=1001(deployer) groups=1001(deployer)
pwd       # Output mong đợi: /home/deployer
```

---

## 5. Đánh giá Mạng, Cổng và Rủi ro Firewall với Docker

### 5.1. Khảo sát các Cổng đang Lắng nghe (Listening Ports)

| Port | Giao thức | Tiến trình / Nguồn gốc | Bind IP | Đánh giá Rủi ro |
| :--- | :--- | :--- | :--- | :--- |
| `22` | TCP | `sshd` (OpenSSH 10.6p1) | `0.0.0.0` & `[::]` | Cổng SSH mở trong toàn bộ mạng LAN Wi-Fi. Cần dùng key authentication và mật khẩu mạnh. |
| `5432` | TCP | `lime_postgres` (Docker proxy) | `0.0.0.0` & `[::]` | Database của dự án khác. Khuyến nghị: nếu chỉ dùng local, nên bind `127.0.0.1:5432`. |
| `6379` | TCP | `lime_redis` (Docker proxy) | `0.0.0.0` & `[::]` | Cache Redis của dự án khác. Nếu Redis không có password, việc bind `0.0.0.0` có rủi ro cao từ mạng LAN. |

### 5.2. Tại sao KHÔNG cài đặt UFW trên máy host Arch Linux này?
1. **Xung đột Kiến trúc với Docker**:
   Docker quản lý mạng container bằng cách tự động chèn các rules và chains vào `iptables`/`nftables` (chain `DOCKER`, `DOCKER-USER`).
2. **Nguy cơ Gây lỗi Dịch vụ Hiện có**:
   Nếu cài và kích hoạt `ufw` một cách máy móc, UFW có thể:
   * Reset hoặc ghi đè các chain của Docker, làm sập kết nối giữa các container `lime_postgres`, `lime_redis`.
   * Hoặc ngược lại, Docker đi vòng qua (bypass) UFW rules do các gói tin NAT đi vào PREROUTING trước khi UFW filter kiểm tra.
3. **Quyết định**: Giữ nguyên cơ chế `iptables-nft` do Docker quản lý, không can thiệp UFW để bảo vệ môi trường làm việc thực tế của máy host.

---

## 6. Sổ tay Xử lý Sự cố SSH Thường gặp (Troubleshooting)

### Vấn đề 1: `Permission denied (publickey)`
* **Nguyên nhân 1: Quyền file quá lỏng lẻo (StrictModes)**:
  OpenSSH daemon từ chối key nếu thư mục `.ssh` hoặc file `authorized_keys` có thể ghi bởi người khác (`group` hoặc `others`).
  * Khắc phục:
    ```bash
    sudo chmod 700 /home/deployer/.ssh
    sudo chmod 600 /home/deployer/.ssh/authorized_keys
    sudo chown -R deployer:deployer /home/deployer/.ssh
    ```
* **Nguyên nhân 2: SSH client dùng nhầm key**:
  SSH client gửi key mặc định `id_ed25519` (GitHub) thay vì key lab.
  * Khắc phục: Luôn dùng cờ `-o IdentitiesOnly=yes`:
    ```bash
    ssh -i ~/.ssh/id_ed25519_cloudops -o IdentitiesOnly=yes deployer@127.0.0.1
    ```

### Vấn đề 2: `WARNING: UNPROTECTED PRIVATE KEY FILE!`
* **Nguyên nhân**: File private key trên máy client có quyền lớn hơn `600` (ví dụ `644` hoặc `777`).
* **Khắc phục**:
  ```bash
  chmod 600 ~/.ssh/id_ed25519_cloudops
  ```
