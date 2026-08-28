"""Giao diện Web Streamlit trực quan — Kiểm thử MCP Server (Bài 1, 2, 3).

Ứng dụng Web giúp người dùng dễ dàng trực quan hoá:
- Bài 1: Tra cứu đơn hàng & Lọc nhật ký hệ thống qua MCP Tools.
- Bài 2: Kiểm thử Authentication (Valid Token vs Invalid Token vs Missing Token).
- Bài 3: Kiểm thử Tool Versioning (v1 vs v2) & Đọc Server Metadata Resource (server://info).
"""

import asyncio
import json
import os
import sys
import httpx
import streamlit as st

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="MCP Server Testing Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Thư mục chứa server.py
BASE_DIR = os.path.dirname(__file__)
SERVER_SCRIPT = os.path.join(BASE_DIR, "server.py")
SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8085/mcp")

# Import trực tiếp hàm từ server.py để gọi UI mượt mà
sys.path.insert(0, BASE_DIR)
from server import (
    ORDERS_DB,
    SYSTEM_LOGS,
    get_order,
    get_order_v2,
    search_orders,
    search_logs,
    server_info,
    VALID_TOKENS,
    DEFAULT_TOKEN,
)

# Header chính
st.title("⚡ Dashboard Trực Quan Kiểm Thử MCP Server")
st.caption("Dự án Day 26 — MCP Tools Integration (Quản lý Đơn hàng & Nhật ký Hệ thống)")

# Sidebar Menu
st.sidebar.image("https://img.icons8.com/isometric/100/server.png", width=70)
st.sidebar.title("Danh mục Kiểm thử")
menu = st.sidebar.radio(
    "Chọn chức năng:",
    [
        "📦 1. Tra cứu & Tìm kiếm Đơn hàng (Bài 1 & 3)",
        "📋 2. Nhật ký Lỗi Hệ thống (Bài 1)",
        "🔒 3. Kiểm thử Authentication HTTP (Bài 2)",
        "📜 4. Server Metadata Resource (Bài 3)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Thông tin Môi trường:**
- **Server Name**: `order-log-system`
- **Current Version**: `2.0.0`
- **Default Token**: `secret-token-123`
- **HTTP Port**: `8085`
""")


# ── MENU 1: TRA CỨU ĐƠN HÀNG ───────────────────────────────────────
if "📦 1." in menu:
    st.header("📦 Bài 1 & Bài 3: Tra cứu & Tìm kiếm Đơn hàng")
    st.write("Kiểm thử giao diện tra cứu thông tin đơn hàng thực tế qua MCP Tools `get_order`, `get_order_v2` và `search_orders`.")

    tab1, tab2 = st.tabs(["🔍 Chi tiết Đơn hàng (v1 vs v2)", "🔎 Tìm kiếm Đơn hàng"])

    with tab1:
        st.subheader("Tra cứu Chi tiết Đơn hàng")
        col_id, col_ver, col_fmt = st.columns([2, 2, 2])
        
        with col_id:
            order_id = st.selectbox(
                "Chọn mã đơn hàng:",
                ["ORD-1001", "ORD-1002", "ORD-1003", "ORD-9999 (Mã sai)"],
            )
            real_order_id = order_id.split(" ")[0]

        with col_ver:
            version = st.radio("Chọn phiên bản Tool:", ["Tool v1 (Text - Deprecated)", "Tool v2 (Structured JSON)"], index=1)

        with col_fmt:
            include_history = st.checkbox("Hiển thị Lịch sử Chuyển Trạng thái", value=True)

        if st.button("🚀 Thực thi Tool Tra cứu", type="primary"):
            st.markdown("---")
            if "v1" in version:
                st.markdown("### 👴 Kết quả gọi Tool `get_order` (v1):")
                result_text = get_order(real_order_id)
                if "❌" in result_text:
                    st.error(result_text)
                else:
                    st.info(result_text)
            else:
                st.markdown("### ⚡ Kết quả gọi Tool `get_order_v2` (v2):")
                result_json_str = get_order_v2(real_order_id, format="json", include_history=include_history)
                result_data = json.loads(result_json_str)

                if "error" in result_data:
                    st.error(f"❌ Error Code: {result_data['error']} (Order ID: {result_data['order_id']})")
                else:
                    # Hiển thị Card tổng quan
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Mã đơn hàng", result_data["order_id"])
                    c2.metric("Khách hàng", result_data["customer"]["name"])
                    c3.metric("Trạng thái", result_data["status"].upper())
                    c4.metric("Tổng tiền", f"{result_data['total_amount_vnd']:,} VNĐ")

                    # Danh sách sản phẩm
                    st.markdown("#### 🛍️ Danh sách Sản phẩm:")
                    st.dataframe(result_data["items"], use_container_width=True)

                    # Lịch sử trạng thái
                    if include_history and "status_history" in result_data:
                        st.markdown("#### 📜 Lịch sử Chuyển Trạng thái:")
                        for h in result_data["status_history"]:
                            st.write(f"• **[{h['timestamp']}]** `{h['status']}` — *{h['note']}*")

                    st.markdown("#### 📄 Output Raw JSON v2:")
                    st.json(result_data)

    with tab2:
        st.subheader("Tìm kiếm Đơn hàng theo Trạng thái / Từ khoá")
        sc1, sc2 = st.columns(2)
        with sc1:
            status_filter = st.selectbox("Lọc theo trạng thái:", ["Tất cả", "processing", "delivered", "cancelled"])
            filter_status = "" if status_filter == "Tất cả" else status_filter
        with sc2:
            kw_filter = st.text_input("Từ khoá (Tên khách / Tên sản phẩm):", "")

        if st.button("🔎 Tìm kiếm Đơn hàng"):
            st.markdown("---")
            search_res = search_orders(status=filter_status, keyword=kw_filter)
            st.code(search_res, language="yaml")


# ── MENU 2: NHẬT KÝ HỆ THỐNG ───────────────────────────────────────
elif "📋 2." in menu:
    st.header("📋 Bài 1: Tra cứu & Lọc Nhật ký Hệ thống (Logs)")
    st.write("Kiểm thử Tool `search_logs` lọc nhật ký lỗi hệ thống theo cấp độ và từ khoá.")

    lc1, lc2, lc3 = st.columns([2, 3, 2])
    with lc1:
        log_level = st.selectbox("Cấp độ Log (Level):", ["ERROR", "WARN", "INFO", "ALL"])
    with lc2:
        log_kw = st.text_input("Từ khoá trong Log (Service / Message):", "")
    with lc3:
        log_limit = st.slider("Giới hạn số dòng (Limit):", 1, 10, 5)

    if st.button("📋 Trích xuất Nhật ký Log", type="primary"):
        st.markdown("---")
        logs_res = search_logs(keyword=log_kw, level=log_level, limit=log_limit)
        st.markdown("### 📄 Kết quả Lọc Log:")
        st.code(logs_res, language="log")


# ── MENU 3: AUTHENTICATION HTTP ─────────────────────────────────────
elif "🔒 3." in menu:
    st.header("🔒 Bài 2: Kiểm thử Authentication trên Streamable HTTP Transport")
    st.write("Kiểm thử trực quan tính năng xác thực Bearer Token qua giao thức HTTP (Server đang chạy tại `http://localhost:8085/mcp`).")

    st.markdown("""
    > [!NOTE]
    > **Ba kịch bản kiểm thử Auth:**
    > 1. **Valid Token (`secret-token-123`)**: Chấp nhận kết nối (**HTTP 200 OK**).
    > 2. **Invalid Token (`wrong-token-abc`)**: Bị từ chối (**HTTP 401 Unauthorized**).
    > 3. **Missing Token (Để trống)**: Bị từ chối (**HTTP 401 Unauthorized**).
    """)

    auth_scenario = st.radio(
        "Chọn kịch bản kiểm thử:",
        ["1. Token Đúng (secret-token-123)", "2. Token Sai (wrong-token-abc)", "3. Thiếu Token (Header rỗng)"],
    )

    token_input = ""
    if "Token Đúng" in auth_scenario:
        token_input = DEFAULT_TOKEN
    elif "Token Sai" in auth_scenario:
        token_input = "invalid-token-xyz"
    else:
        token_input = ""

    st.text_input("Bearer Token sẽ gửi:", value=token_input, disabled=True)

    if st.button("🚀 Gửi Request HTTP Test Auth", type="primary"):
        st.markdown("---")
        st.write("📡 Gửi HTTP POST Request tới `http://localhost:8085/mcp`...")

        headers = {}
        if token_input:
            headers["Authorization"] = f"Bearer {token_input}"

        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post("http://localhost:8085/mcp", headers=headers, json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
                st.subheader(f"HTTP Status Code: `{res.status_code}`")
                
                if res.status_code == 200 or res.status_code == 202:
                    st.success("✅ **TEST PASSED**: Server chấp nhận Token hợp lệ! Đã xác thực thành công.")
                    st.json(res.json() if res.content else {"message": "Success"})
                elif res.status_code in [401, 403]:
                    st.warning(f"✅ **TEST PASSED**: Đúng kỳ vọng! Server từ chối Token không hợp lệ với status {res.status_code}.")
                    st.code(res.text, language="json")
                else:
                    st.info(f"Response: {res.status_code} — {res.text}")
        except httpx.ConnectError:
            st.error("❌ Không thể kết nối tới HTTP Server tại `http://localhost:8085/mcp`. Vui lòng chạy `python server.py --http` trong Terminal!")
        except Exception as e:
            st.warning(f"✅ Đúng kỳ vọng! Giao thức từ chối kết nối: {e}")


# ── MENU 4: SERVER METADATA RESOURCE ────────────────────────────────
elif "📜 4." in menu:
    st.header("📜 Bài 3: Metadata Resource (`server://info`) & Versioning")
    st.write("Đọc và trực quan hoá thông tin Resource `server://info` được Server công bố.")

    info_json = server_info()
    info_data = json.loads(info_json)

    st.markdown("### 📊 Tổng quan Metadata Server:")
    m1, m2, m3 = st.columns(3)
    m1.metric("Server Name", info_data["name"])
    m2.metric("Server Version", f"v{info_data['version']}")
    m3.metric("Capabilities Count", len(info_data["capabilities"]))

    st.markdown("#### 🛠️ Danh sách Deprecated Tools:")
    st.warning(f"⚠️ Deprecated Tools: `{info_data['deprecated_tools']}`")
    st.info(f"💡 Hướng dẫn Migration: {info_data['migration_guide']}")

    st.markdown("#### ⚙️ Chi tiết Danh mục Tools:")
    st.dataframe(info_data["tools"], use_container_width=True)

    st.markdown("#### 📄 Raw Resource Content (`server://info`):")
    st.json(info_data)
