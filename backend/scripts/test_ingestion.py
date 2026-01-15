import httpx
import json

# Configuration
API_URL = "http://localhost:8000/api/v1/internal/ingest/batch"
TOKEN = "test-token-123" # We will set this in .env

# Sample Data
payload = {
    "translations": [
        {
            "arxiv_id": "2512.23903v1",
            "title_zh": "测试翻译标题",
            "summary_zh": "这是由本地生产服务器生成的测试翻译摘要。",
            "model_name": "gpt-4o"
        }
    ],
    "interpretations": [
        {
            "arxiv_id": "2512.23903v1",
            "interpretation": "## 核心贡献\n该论文提出了一种新的方法...\n## 技术细节\n使用了卷积神经网络...",
            "language": "zh",
            "model_name": "gpt-4o"
        }
    ],
    "tts_records": [
        {
            "arxiv_id": "2512.23903v1",
            "file_url": "https://cos.ap-guangzhou.myqcloud.com/example/audio.mp3",
            "file_size": 102456,
            "voice_model": "zh-CN-XiaoxiaoNeural",
            "content_hash": "hash123"
        }
    ]
}

def test_ingestion():
    headers = {
        "X-Internal-Token": TOKEN,
        "Content-Type": "application/json"
    }
    
    print(f"Sending request to {API_URL}...")
    try:
        response = httpx.post(API_URL, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ingestion()
