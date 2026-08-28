"""OpenRouter MCP Client cho Lab 04.

Kết nối tới Weather MCP Server qua Streamable HTTP, tự động hỏi list_tools từ MCP Server,
chuyển đổi sang format OpenAI/OpenRouter tools, nhờ OpenRouter Model chọn tool và gọi lại MCP Server.

Cách chạy:
    1. Mở Terminal 1 (chạy MCP Server):
       cd 04-lab/mcp-server
       $env:WEATHERAPI_KEY="your_key"  (nếu có)
       python weather.py

    2. Mở Terminal 2 (chạy Client này với OpenRouter Key):
       $env:OPENROUTER_API_KEY="sk-or-v1-..."
       cd 04-lab
       python openrouter_mcp_client.py
"""

import asyncio
import json
import os
import sys
import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

# Hỗ trợ hiển thị UTF-8 / Emoji trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def main():
    if not OPENROUTER_API_KEY:
        print("❌ Lỗi: Chưa thiết lập biến môi trường OPENROUTER_API_KEY!")
        print("Cách set key (PowerShell): $env:OPENROUTER_API_KEY=\"sk-or-v1-...\"")
        sys.exit(1)

    print(f"🔌 Đang kết nối tới MCP Server tại {MCP_SERVER_URL}...")

    try:
        async with streamable_http_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("✅ Kết nối MCP Server thành công!")

                # 1. Khám phá tools từ MCP Server
                mcp_tools_result = await session.list_tools()
                openrouter_tools = []

                print("\n🛠️ Tools khám phá được từ MCP Server:")
                for tool in mcp_tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                    openrouter_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.input_schema
                                or {"type": "object", "properties": {}},
                            },
                        }
                    )

                # 2. Câu hỏi của người dùng
                user_question = "Thời tiết hiện tại ở Hà Nội thế nào? Và dự báo 2 ngày tới ra sao?"
                print(f"\n💬 Người dùng hỏi: '{user_question}'")

                messages = [
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý thời tiết thông minh. Dùng các tools được cung cấp để trả lời bằng tiếng Việt thân thiện.",
                    },
                    {"role": "user", "content": user_question},
                ]

                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": MODEL,
                    "messages": messages,
                    "tools": openrouter_tools,
                    "max_tokens": 1000,
                }

                # 3. Gửi câu hỏi kèm MCP tools đến OpenRouter
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        OPENROUTER_URL, headers=headers, json=payload
                    )
                    res_data = resp.json()

                    if "error" in res_data:
                        print(f"❌ Lỗi OpenRouter API: {res_data['error']}")
                        return

                    message = res_data["choices"][0]["message"]

                    # 4. Vòng lặp điều phối: Nếu OpenRouter yêu cầu gọi tool
                    while message.get("tool_calls"):
                        messages.append(message)
                        for tool_call in message["tool_calls"]:
                            func_name = tool_call["function"]["name"]
                            func_args = json.loads(
                                tool_call["function"]["arguments"]
                            )
                            print(
                                f"\n🤖 OpenRouter Model đề xuất gọi MCP Tool: {func_name}({func_args})"
                            )

                            # Gọi tool trực tiếp trên MCP Server
                            tool_result = await session.call_tool(
                                func_name, func_args
                            )
                            result_text = (
                                tool_result.content[0].text
                                if tool_result.content
                                else ""
                            )
                            print(
                                f"📡 Kết quả từ MCP Server trả về:\n{result_text.strip()}"
                            )

                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "name": func_name,
                                    "content": result_text,
                                }
                            )

                        # Gửi lại kết quả tool cho OpenRouter để tổng hợp câu trả lời
                        payload["messages"] = messages
                        resp = await client.post(
                            OPENROUTER_URL, headers=headers, json=payload
                        )
                        res_data = resp.json()
                        message = res_data["choices"][0]["message"]

                    print(
                        f"\n✨ Câu trả lời hoàn chỉnh từ OpenRouter LLM:\n{message.get('content')}"
                    )

    except Exception as e:
        import traceback
        print(
            f"❌ Không thể kết nối MCP Server tại {MCP_SERVER_URL}. Vui lòng kiểm tra lại Server!"
        )
        print(f"Chi tiết lỗi: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
