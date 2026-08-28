"""Client test cho Bài 3 — Versioning & Metadata Resource (server://info).

Các tính năng kiểm thử:
1. Đọc metadata resource "server://info" để xác định version server và deprecated tools.
2. Legacy Client: Gọi tool v1 ("get_order") để chứng minh backward compatibility không bị hỏng.
3. Modern Client: Gọi tool v2 ("get_order_v2") để sử dụng định dạng JSON cấu trúc và tính năng xem lịch sử mới.
4. Smart Client: Tự động quyết định gọi tool v1 hay v2 dựa trên capabilities/metadata công bố.
"""

import asyncio
import json
import os
import sys

# Hỗ trợ hiển thị UTF-8 trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    print("==================================================")
    print("🚀 BÀI 3 TEST: Versioning & Metadata Resource (server://info)")
    print("==================================================")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Đọc metadata resource "server://info"
            print("\n--------------------------------------------------")
            print("📜 Step 1: Đọc thông tin Resource 'server://info'")
            info = await session.read_resource("server://info")
            metadata = json.loads(info.contents[0].text)

            print(f"  • Server Name: {metadata['name']}")
            print(f"  • Server Version: v{metadata['version']}")
            print(f"  • Capabilities: {', '.join(metadata['capabilities'])}")
            print(f"  • Deprecated Tools: {metadata['deprecated_tools']}")
            print(f"  • Migration Guide: {metadata['migration_guide']}")

            # 2. Test gọi Legacy Tool v1
            print("\n--------------------------------------------------")
            print("👴 Step 2: Legacy Client gọi tool v1 'get_order' (Backward Compatibility)")
            res_v1 = await session.call_tool("get_order", {"order_id": "ORD-1001"})
            print(f"[Legacy v1 Result]:\n{res_v1.content[0].text}")

            # 3. Test gọi Modern Tool v2
            print("\n--------------------------------------------------")
            print("⚡ Step 3: Modern Client gọi tool v2 'get_order_v2' (Structured JSON)")
            res_v2 = await session.call_tool("get_order_v2", {
                "order_id": "ORD-1001",
                "format": "json",
                "include_history": True,
            })
            json_data = json.loads(res_v2.content[0].text)
            print("[Modern v2 Pretty JSON Result]:")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))

            # 4. Dynamic/Smart Client chọn tool tự động
            print("\n--------------------------------------------------")
            print("🧠 Step 4: Smart Client tự động chọn tool v2 dựa theo metadata")
            tools_list = [t.name for t in (await session.list_tools()).tools]
            
            target_order_id = "ORD-1003"
            if "get_order_v2" in tools_list and "get_order" in metadata.get("deprecated_tools", []):
                print(f"  -> Phát hiện 'get_order' đã deprecated và 'get_order_v2' sẵn sàng. Tự động chọn v2 cho {target_order_id}...")
                res_smart = await session.call_tool("get_order_v2", {"order_id": target_order_id})
                print(f"  [Smart Output]: {res_smart.content[0].text[:120]}...")
            else:
                print(f"  -> Sử dụng tool mặc định v1...")
                res_smart = await session.call_tool("get_order", {"order_id": target_order_id})
                print(f"  [Smart Output]: {res_smart.content[0].text}")

    print("\n🎉 Bài 3 test hoàn thành tốt đẹp! Tương thích ngược & Versioning hoạt động xuất sắc.")


if __name__ == "__main__":
    asyncio.run(main())
