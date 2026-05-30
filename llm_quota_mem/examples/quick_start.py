import httpx
import asyncio
import json

async def verify_server():
    print("🚀 Verifying llm-quota-mem Unified Server...")

    url = "http://localhost:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Is the unified LLM server running correctly?"}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First check health
            health = await client.get("http://localhost:8000/health")
            print(f"Health Check: {health.json()}")

            # Then try a chat completion
            print("Sending test chat completion request...")
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("\n✅ Server is UP and responding!")
                print(f"Response: {content}")
            else:
                print(f"❌ Server returned error {response.status_code}: {response.text}")

    except httpx.ConnectError:
        print("❌ Could not connect to the server. Make sure to run 'python -m llm_quota_mem.app' first.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(verify_server())
