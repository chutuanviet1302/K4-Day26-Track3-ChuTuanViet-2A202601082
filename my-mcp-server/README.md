# 🚀 Custom MCP Server — Tra cứu Đơn hàng & Nhật ký Lỗi Hệ thống

Dự án MCP Server thực tế được phát triển cho bài tập **Day 26 - MCP Tools Integration**.

---

## 📌 Bước 1: Use Case Cá nhân
- **Công việc hiện tại**: Tra cứu thông tin đơn hàng bán hàng và kiểm tra nhật ký lỗi hệ thống hàng ngày.
- **Tôi đang làm thủ công như thế nào**: 
  - Mở file danh sách đơn hàng để tra cứu thông tin theo mã đơn `ORD-XXXX` hoặc xem trạng thái đơn hàng.
  - Mở file log trên server để lọc các dòng nhật ký chứa cấp độ lỗi `ERROR` nhằm phát hiện sự cố hệ thống.
- **Input**:
  - `order_id`: Mã đơn hàng (ví dụ: `ORD-1001`, `ORD-1002`).
  - `status`: Trạng thái đơn hàng (`processing`, `delivered`, `cancelled`).
  - `level`: Cấp độ log (`ERROR`, `WARN`, `INFO`).
  - `keyword`: Từ khoá tìm kiếm tên khách hàng, tên sản phẩm hoặc nội dung log.
- **Output**: Thông tin đơn hàng chi tiết, lịch sử trạng thái đơn hàng, hoặc danh sách các log lỗi gần nhất kèm mốc thời gian.

---

## 🛠️ Bước 2: Thiết kế MCP Tools

MCP Server cung cấp các tools thực tế sau:

| Tool | Input Parameters | Output Format | Description |
|---|---|---|---|
| `get_order` | `order_id: str` | Plain text | Tra cứu thông tin đơn hàng v1 (Legacy tool). |
| `get_order_v2` | `order_id: str`, `format: str = "json"`, `include_history: bool = True` | JSON / Text | Tra cứu thông tin đơn hàng v2 (Rich JSON + Status History). |
| `search_orders` | `status: str = ""`, `keyword: str = ""` | Formatted text | Tìm kiếm danh sách đơn hàng theo trạng thái hoặc từ khoá. |
| `search_logs` | `keyword: str = ""`, `level: str = "ERROR"`, `limit: int = 10` | Formatted log lines | Lọc nhật ký lỗi hệ thống theo cấp độ và từ khoá. |

---

## ⚡ Bước 3: Cách Chạy Server

### 1. Chế độ stdio (Mặc định cho Claude Code / CLI MCP Client)
```bash
python server.py
```

### 2. Chế độ Streamable HTTP Server (Hỗ trợ Remote Remote / LAN / Authentication)
```bash
python server.py --http
```
Server sẽ chạy tại `http://localhost:8085/mcp`.

---

## 🤖 Bước 4: Đăng ký với Claude Code / Claude Desktop

Thêm cấu hình sau vào file cấu hình của Claude Code (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "python",
      "args": [
        "d:/Program Files/Downloads/2026 work/ai in action/lab/lab26/K4-Day26-Track3-ChuTuanViet-2A202601082/my-mcp-server/server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Yêu cầu bằng ngôn ngữ tự nhiên với Claude Code:
- *"Tìm giúp tôi 3 lỗi ERROR gần nhất trong log hệ thống."*
- *"Tra cứu giúp tôi đơn hàng ORD-1001 xem đã thanh toán chưa."*
- *"Tìm danh sách các đơn hàng đang ở trạng thái processing."*

---

## 🔒 Bước 5: Authentication (Streamable HTTP Transport)

Server tích hợp lớp `StaticTokenVerifier` để bảo mật mọi kết nối HTTP qua header `Authorization: Bearer <token>`.

- **Bearer Token mặc định**: `secret-token-123`

### Kiểm thử Authentication:
Chạy script kiểm thử tự động 3 kịch bản:
```bash
python test_auth_client.py
```
- ✅ **Valid Token**: Kết nối thành công, cho phép thực thi tools.
- ❌ **Invalid Token**: Server từ chối truy cập ngay lập tức với **HTTP 401 Unauthorized**.
- ❌ **Missing Token**: Server từ chối truy cập ngay lập tức với **HTTP 401 Unauthorized**.

---

## 🔄 Bước 6: Tool Versioning & Server Metadata Resource

Server hỗ trợ Resource `server://info` công bố metadata phục vụ kiểm tra khả năng tương thích ngược (Backward Compatibility):

### 1. Resource Metadata (`server://info`)
```json
{
  "name": "my-mcp-server",
  "version": "2.0.0",
  "capabilities": ["tools", "resources", "authentication", "versioning"],
  "deprecated_tools": ["get_order"],
  "migration_guide": "Vui lòng chuyển từ 'get_order' sang 'get_order_v2'..."
}
```

### 2. Tương thích ngược (Backward Compatibility)
- **v1 (`get_order`)**: Giữ nguyên cho các client cũ hoạt động không bị break.
- **v2 (`get_order_v2`)**: Cung cấp cấu trúc JSON giàu thông tin kèm lịch sử đơn hàng.
- **Smart Client (`test_versioned_client.py`)**: Đọc `server://info`, kiểm tra version và ưu tiên tự động gọi `get_order_v2`.

Chạy test Versioning:
```bash
python test_versioned_client.py
```

---

## 📦 Bước 7: Cập nhật & Push Code lên Git Repository

```bash
git status
git add .
git commit -m "Complete Day26 MCP Tools Integration - All 7 Steps"
git push
```
