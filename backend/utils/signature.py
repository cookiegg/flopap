import os
import hmac
import hashlib
import time

def generate_cos_signature(method, uri, expires=21600):
    """生成COS访问签名"""
    secret_key = os.getenv('TX_COS_SIGNATURE_KEY')
    timestamp = int(time.time()) + expires
    string_to_sign = f"{method}\n{uri}\n{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{timestamp}.{signature}"

# 在你的API路由中使用
def get_tts_url(paper_id, segment):
    file_path = f"/tts/tts_opus/{paper_id}_{segment}.opus"
    signature = generate_cos_signature("GET", file_path)
    signed_url = f"https://cdn.flopap.com{file_path}?sig={signature}"
    return {"url": signed_url}
