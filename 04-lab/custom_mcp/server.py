"""Custom MCP Server — Quản lý Đơn hàng & Nhật ký Hệ thống (Order & System Log Management).

Triển khai đầy đủ 3 bài tập:
- Bài 1: Viết MCP Server với các tools thực tế (get_order, search_orders, search_logs).
- Bài 2: Hỗ trợ Authentication qua HTTP (Streamable HTTP với Bearer Token).
- Bài 3: Hỗ trợ Versioning (v1, v2, resource server://info).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

# Hỗ trợ hiển thị UTF-8 / Emoji trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_VERSION = "2.0.0"
DEFAULT_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "secret-token-123")

# --- Danh sách Token hợp lệ (Bài 2) ---
VALID_TOKENS: dict[str, str] = {
    DEFAULT_TOKEN: "admin-user",
    "dev-token-abc123": "dev-user",
}


class StaticTokenVerifier(TokenVerifier):
    """Xác minh Bearer Token tĩnh cho Streamable HTTP transport (Bài 2)."""

    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = VALID_TOKENS.get(token)
        if client_id is None:
            return None
        return AccessToken(token=token, client_id=client_id, scopes=["orders:read", "logs:read"])


# --- Khởi tạo MCP Server ---
port = int(os.getenv("PORT", 8085))

mcp = MCPServer(
    "order-log-system",
    instructions=f"MCP Server v{SERVER_VERSION} cho công việc quản lý đơn hàng & nhật ký hệ thống.",
    auth=AuthSettings(
        issuer_url=f"http://localhost:{port}",
        resource_server_url=f"http://localhost:{port}",
    ),
    token_verifier=StaticTokenVerifier(),
)


# ── MOCK DATABASE ──────────────────────────────────────────────────
ORDERS_DB: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_name": "Nguyễn Văn A",
        "email": "nva@example.com",
        "status": "processing",
        "items": [
            {"sku": "LAPTOP-01", "name": "Laptop Dell XPS 15", "quantity": 1, "price": 35000000},
            {"sku": "MOUSE-02", "name": "Chuột Logitech MX Master 3S", "quantity": 1, "price": 2500000},
        ],
        "total_amount": 37500000,
        "created_at": "2026-08-25T09:30:00Z",
        "shipping_address": "123 Đường Lê Lợi, Quận 1, TP. Hồ Chí Minh",
        "history": [
            {"status": "created", "timestamp": "2026-08-25T09:30:00Z", "note": "Đơn hàng đã được tạo"},
            {"status": "processing", "timestamp": "2026-08-25T10:15:00Z", "note": "Đã xác nhận thanh toán qua VNPay"},
        ],
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_name": "Trần Thị B",
        "email": "ttb@example.com",
        "status": "delivered",
        "items": [
            {"sku": "PHONE-01", "name": "iPhone 15 Pro Max 256GB", "quantity": 1, "price": 30000000},
        ],
        "total_amount": 30000000,
        "created_at": "2026-08-20T14:20:00Z",
        "shipping_address": "456 Đường Cầu Giấy, Quận Cầu Giấy, Hà Nội",
        "history": [
            {"status": "created", "timestamp": "2026-08-20T14:20:00Z", "note": "Đơn hàng đã được tạo"},
            {"status": "shipped", "timestamp": "2026-08-21T08:00:00Z", "note": "Đã giao cho đơn vị vận chuyển GHN"},
            {"status": "delivered", "timestamp": "2026-08-22T16:45:00Z", "note": "Khách hàng đã nhận hàng thành công"},
        ],
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_name": "Lê Văn C",
        "email": "lvc@example.com",
        "status": "cancelled",
        "items": [
            {"sku": "MONITOR-01", "name": "Màn hình LG UltraGear 27 inch", "quantity": 2, "price": 8000000},
        ],
        "total_amount": 16000000,
        "created_at": "2026-08-27T11:00:00Z",
        "shipping_address": "789 Đường Nguyễn Văn Linh, Hải Phòng",
        "history": [
            {"status": "created", "timestamp": "2026-08-27T11:00:00Z", "note": "Đơn hàng đã được tạo"},
            {"status": "cancelled", "timestamp": "2026-08-27T11:30:00Z", "note": "Khách hàng yêu cầu hủy đơn"},
        ],
    },
}

SYSTEM_LOGS: list[dict[str, str]] = [
    {"timestamp": "2026-08-28T13:40:00Z", "level": "ERROR", "service": "payment-gateway", "message": "VNPay API timeout after 30s for transaction TX-9921"},
    {"timestamp": "2026-08-28T13:35:12Z", "level": "WARN", "service": "inventory-service", "message": "Low stock alert for SKU LAPTOP-01: remaining 2 items"},
    {"timestamp": "2026-08-28T13:30:00Z", "level": "ERROR", "service": "auth-service", "message": "Failed login attempt limit exceeded for IP 192.168.1.105"},
    {"timestamp": "2026-08-28T13:25:44Z", "level": "INFO", "service": "order-service", "message": "Order ORD-1001 status changed to processing"},
    {"timestamp": "2026-08-28T13:10:05Z", "level": "ERROR", "service": "database", "message": "Connection pool exhausted on postgres-replica-01"},
]


# ── BÀI 1 & BÀI 3: TOOLS ───────────────────────────────────────────

@mcp.tool()
def get_order(order_id: str) -> str:
    """[v1 - Deprecated] Tra cứu thông tin đơn hàng theo mã đơn (trả về văn bản đơn giản).

    Args:
        order_id: Mã đơn hàng (ví dụ: ORD-1001, ORD-1002, ORD-1003)
    """
    order = ORDERS_DB.get(order_id.upper())
    if not order:
        return f"❌ Không tìm thấy đơn hàng có mã '{order_id}'."

    items_str = ", ".join([f"{item['name']} (x{item['quantity']})" for item in order['items']])
    return (
        f"📦 Đơn hàng {order['order_id']}:\n"
        f"- Khách hàng: {order['customer_name']}\n"
        f"- Trạng thái: {order['status'].upper()}\n"
        f"- Sản phẩm: {items_str}\n"
        f"- Tổng tiền: {order['total_amount']:,} VNĐ\n"
        f"- Địa chỉ: {order['shipping_address']}"
    )


@mcp.tool()
def get_order_v2(
    order_id: str,
    format: str = "json",
    include_history: bool = True,
) -> str:
    """[v2] Tra cứu đơn hàng chi tiết — Trả về JSON cấu trúc, hỗ trợ xem lịch sử và tùy chọn định dạng.

    Args:
        order_id: Mã đơn hàng (ví dụ: ORD-1001, ORD-1002, ORD-1003)
        format: Định dạng trả về ("json" hoặc "text", mặc định: "json")
        include_history: Có kèm lịch sử chuyển trạng thái không (mặc định: True)
    """
    order = ORDERS_DB.get(order_id.upper())
    if not order:
        error_res = {"error": "ORDER_NOT_FOUND", "order_id": order_id, "api_version": "2.0"}
        return json.dumps(error_res, ensure_ascii=False) if format == "json" else f"❌ Error: Order {order_id} not found."

    result = {
        "api_version": "2.0",
        "order_id": order["order_id"],
        "customer": {
            "name": order["customer_name"],
            "email": order["email"],
        },
        "status": order["status"],
        "total_amount_vnd": order["total_amount"],
        "items": order["items"],
        "shipping_address": order["shipping_address"],
        "created_at": order["created_at"],
    }

    if include_history:
        result["status_history"] = order["history"]

    if format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        history_str = "\n".join([f"  • [{h['timestamp']}] {h['status']}: {h['note']}" for h in order['history']]) if include_history else "N/A"
        return f"[v2 Text Format]\nOrder {result['order_id']} | Status: {result['status']}\nCustomer: {order['customer_name']} <{order['email']}>\nHistory:\n{history_str}"


@mcp.tool()
def search_orders(status: str = "", keyword: str = "") -> str:
    """Tìm kiếm đơn hàng theo trạng thái hoặc từ khoá (tên khách hàng, tên sản phẩm).

    Args:
        status: Trạng thái đơn hàng ("processing", "delivered", "cancelled" hoặc "" để lấy tất cả)
        keyword: Từ khoá tìm kiếm theo tên khách hàng hoặc tên sản phẩm
    """
    results = []
    for order in ORDERS_DB.values():
        match_status = not status or order["status"].lower() == status.lower()
        match_kw = not keyword or (
            keyword.lower() in order["customer_name"].lower()
            or any(keyword.lower() in item["name"].lower() for item in order["items"])
        )
        if match_status and match_kw:
            results.append(order)

    if not results:
        return f"🔍 Không tìm thấy đơn hàng khớp với trạng thái='{status}', từ khoá='{keyword}'."

    summary = [f"Found {len(results)} order(s):"]
    for o in results:
        items_summary = ", ".join([item["name"] for item in o["items"]])
        summary.append(f"• [{o['order_id']}] {o['customer_name']} | Status: {o['status']} | Total: {o['total_amount']:,} VNĐ | Items: {items_summary}")

    return "\n".join(summary)


@mcp.tool()
def search_logs(keyword: str = "", level: str = "ERROR", limit: int = 10) -> str:
    """Tìm kiếm và lọc nhật ký hệ thống (logs).

    Args:
        keyword: Từ khoá tìm trong message hoặc service (ví dụ: "timeout", "payment")
        level: Cấp độ log ("ERROR", "WARN", "INFO", hoặc "ALL")
        limit: Số lượng dòng log tối đa trả về (mặc định: 10)
    """
    filtered = []
    for log in SYSTEM_LOGS:
        match_level = level.upper() == "ALL" or log["level"].upper() == level.upper()
        match_kw = not keyword or (
            keyword.lower() in log["message"].lower()
            or keyword.lower() in log["service"].lower()
        )
        if match_level and match_kw:
            filtered.append(log)

    filtered = filtered[:limit]
    if not filtered:
        return f"📝 Không tìm thấy log khớp với level='{level}', keyword='{keyword}'."

    lines = [f"📋 Found {len(filtered)} log entry/entries (Level: {level}):"]
    for l in filtered:
        lines.append(f"[{l['timestamp']}] [{l['level']}] [{l['service']}] {l['message']}")

    return "\n".join(lines)


# ── BÀI 3: RESOURCE SERVER METADATA ────────────────────────────────

@mcp.resource("server://info")
def server_info() -> str:
    """Metadata công bố thông tin server, version, capabilities và hướng dẫn migration."""
    metadata = {
        "name": "order-log-system",
        "version": SERVER_VERSION,
        "description": "MCP Server cho công việc tra cứu đơn hàng & nhật ký hệ thống.",
        "capabilities": ["tools", "resources", "authentication", "versioning"],
        "deprecated_tools": ["get_order"],
        "migration_guide": "Vui lòng chuyển từ 'get_order' sang 'get_order_v2' để có dữ liệu JSON cấu trúc và xem lịch sử trạng thái.",
    }
    return json.dumps(metadata, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    is_http_mode = "--http" in sys.argv or os.getenv("MCP_TRANSPORT") == "http"

    if is_http_mode:
        print(f"🚀 [HTTP Mode] Starting Streamable HTTP MCP Server on http://0.0.0.0:{port}/mcp")
        print(f"🔑 Required Bearer Token: {DEFAULT_TOKEN}")
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        print("⚡ [Stdio Mode] Starting MCP Server over stdio...", file=sys.stderr)
        mcp.run()
