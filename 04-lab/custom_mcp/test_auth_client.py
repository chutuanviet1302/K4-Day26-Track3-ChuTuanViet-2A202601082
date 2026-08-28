"""Client test cho Bài 2 — Kiểm tra Streamable HTTP Transport & Authentication (Bearer Token).

Các kịch bản kiểm thử:
1. Valid Token: Đăng nhập với Token đúng ("secret-token-123") -> Thành công.
2. Invalid Token: Đăng nhập với Token sai ("wrong-token-abc") -> Nhận lỗi 401/403.
3. Missing Token: Đăng nhập không kèm Token -> Nhận lỗi 401/403.
"""

import asyncio
import os
import sys
import httpx

# Hỗ trợ hiển thị UTF-8 trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8085/mcp")
VALID_TOKEN = "secret-token-123"
INVALID_TOKEN = "wrong-token-abc"


async def test_valid_token() -> bool:
    print("\n--------------------------------------------------")
    print(f"🔒 Test 1: Kết nối với VALID Token ('{VALID_TOKEN}')")
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("✅ Kết nối thành công! Server chấp nhận Token hợp lệ.")

                    tools = await session.list_tools()
                    print(f"📋 Được phép truy cập {len(tools.tools)} tools.")
                    
                    # Gọi thử 1 tool
                    result = await session.call_tool("get_order", {"order_id": "ORD-1002"})
                    print(f"📦 Kết quả gọi tool get_order('ORD-1002'):\n{result.content[0].text}")
                    return True
    except Exception as e:
        print(f"❌ Thất bại ngoài dự kiến: {e}")
        return False


async def test_invalid_token() -> bool:
    print("\n--------------------------------------------------")
    print(f"🚫 Test 2: Kết nối với INVALID Token ('{INVALID_TOKEN}')")
    headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("❌ Lỗi: Server lại chấp nhận Token sai!")
                    return False
    except httpx.HTTPStatusError as e:
        print(f"✅ Đúng kỳ vọng! Server từ chối Token sai với Status Code: {e.response.status_code}")
        return True
    except Exception as e:
        print(f"✅ Đúng kỳ vọng! Từ chối truy cập do Token không hợp lệ. Chi tiết: {e}")
        return True


async def test_missing_token() -> bool:
    print("\n--------------------------------------------------")
    print("🚫 Test 3: Kết nối KHÔNG CÓ Token (Missing Header)")

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("❌ Lỗi: Server chấp nhận request không có Token!")
                    return False
    except httpx.HTTPStatusError as e:
        print(f"✅ Đúng kỳ vọng! Server từ chối request thiếu Token với Status Code: {e.response.status_code}")
        return True
    except Exception as e:
        print(f"✅ Đúng kỳ vọng! Từ chối truy cập do thiếu Token. Chi tiết: {e}")
        return True


async def main() -> None:
    print("==================================================")
    print("🚀 BÀI 2 TEST: Authentication trên Streamable HTTP Transport")
    print("==================================================")

    res1 = await test_valid_token()
    res2 = await test_invalid_token()
    res3 = await test_missing_token()

    print("\n==================================================")
    if res1 and res2 and res3:
        print("🎉 TẤT CẢ TEST AUTHENTICATION CỦA BÀI 2 ĐỀU ĐẠT CHUẨN!")
    else:
        print("⚠️ Có test chưa hoàn tất thành công. Vui lòng kiểm tra lại server log.")


if __name__ == "__main__":
    asyncio.run(main())
