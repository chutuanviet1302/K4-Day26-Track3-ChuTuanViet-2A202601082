"""Client test cho Bài 1 — Kết nối MCP Server qua stdio transport."""

import asyncio
import os
import sys

# Hỗ trợ hiển thị UTF-8 trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    
    # Cấu hình stdio parameters để khởi chạy server.py qua python
    params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    print("==================================================")
    print("🚀 BÀI 1 TEST: Kết nối MCP Server qua stdio transport")
    print("==================================================")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Đã khởi tạo MCP Session thành công!")

            # 1. Liệt kê các tool hiện có
            tools_response = await session.list_tools()
            print(f"\n📋 Danh sách tools sẵn có ({len(tools_response.tools)} tools):")
            for t in tools_response.tools:
                print(f"  • {t.name}: {t.description.splitlines()[0] if t.description else ''}")

            # 2. Gọi tool get_order (Tra cứu đơn hàng)
            print("\n--------------------------------------------------")
            print("🔍 Test 1: Gọi tool 'get_order' cho đơn ORD-1001")
            res_order = await session.call_tool("get_order", {"order_id": "ORD-1001"})
            print(res_order.content[0].text)

            # 3. Gọi tool search_orders (Tìm kiếm đơn hàng)
            print("\n--------------------------------------------------")
            print("🔍 Test 2: Gọi tool 'search_orders' với status='processing'")
            res_search = await session.call_tool("search_orders", {"status": "processing"})
            print(res_search.content[0].text)

            # 4. Gọi tool search_logs (Tra cứu log hệ thống)
            print("\n--------------------------------------------------")
            print("🔍 Test 3: Gọi tool 'search_logs' cho level='ERROR'")
            res_logs = await session.call_tool("search_logs", {"level": "ERROR", "limit": 3})
            print(res_logs.content[0].text)

    print("\n🎉 Bài 1 test hoàn thành tốt đẹp!")


if __name__ == "__main__":
    asyncio.run(main())
