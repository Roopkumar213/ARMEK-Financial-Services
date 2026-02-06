from llm_factory import get_llm_client, LLM_MODEL

def test_connection():
    print(f"Testing connection to {LLM_MODEL}...")
    client = get_llm_client()
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "Hello, are you online?"}],
            max_tokens=50
        )
        print("✅ SUCCESS!")
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ FAILED")
        print(e)

if __name__ == "__main__":
    test_connection()
