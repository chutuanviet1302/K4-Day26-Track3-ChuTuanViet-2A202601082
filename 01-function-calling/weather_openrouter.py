"""Minh họa FUNCTION CALLING thuần với OpenRouter API (OpenAI-compatible format).

Dùng OpenRouter API key để gọi Gemini / GPT / Llama models qua OpenRouter.
Tool `get_weather` được định nghĩa schema chuẩn OpenAI VÀ thực thi ngay trong app này.

Cách chạy:
    $env:OPENROUTER_API_KEY="sk-or-v1-..."  (Windows PowerShell)
    python weather_openrouter.py
"""

import json
import os
import sys
import httpx

# Hỗ trợ hiển thị UTF-8 / Emoji trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Lấy API key từ môi trường
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ Lỗi: Chưa thiết lập biến môi trường OPENROUTER_API_KEY!")
    print("Cách set key (PowerShell): $env:OPENROUTER_API_KEY=\"sk-or-v1-...\"")
    sys.exit(1)

# Model hỗ trợ Tool/Function Calling trên OpenRouter
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế."
)

# 1. App tự định nghĩa schema của tool (Chuẩn OpenAI/OpenRouter)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố (ví dụ: Hà Nội, Hồ Chí Minh, Đà Nẵng)"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. Hàm thực thi tool tại App
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của city."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


def run(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "max_tokens": 1000
    }

    # 3. Gửi request tới OpenRouter
    with httpx.Client(timeout=30.0) as client:
        response = client.post(OPENROUTER_URL, headers=headers, json=payload)
        res_data = response.json()

        if "error" in res_data:
            return f"❌ Lỗi OpenRouter API: {res_data['error']}"

        choice = res_data["choices"][0]
        message = choice["message"]

        # 4. Vòng lặp: Nếu model yêu cầu tool_calls, App TỰ THỰC THI rồi gửi kết quả lại
        while message.get("tool_calls"):
            messages.append(message)  # Lưu lại phản hồi chứa tool call của model

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                print(f"  [OpenRouter Model đề xuất call tool] {func_name}({func_args})")

                if func_name == "get_weather":
                    result = get_weather(**func_args)
                    print(f"  [App tự chạy hàm local]             -> {result}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": func_name,
                        "content": result
                    })

            # Gửi lại lịch sử cuộc thoại kèm kết quả tool cho OpenRouter
            payload["messages"] = messages
            response = client.post(OPENROUTER_URL, headers=headers, json=payload)
            res_data = response.json()
            message = res_data["choices"][0]["message"]

        return message.get("content", "")


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"Sử dụng OpenRouter với model: {MODEL}")
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
