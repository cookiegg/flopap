"""简单的频率限制中间件"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from typing import Dict, Tuple

# 内存存储（生产环境应该用 Redis）
request_counts: Dict[str, Tuple[int, datetime]] = defaultdict(lambda: (0, datetime.now()))

def get_client_id(request: Request) -> str:
    """获取客户端标识"""
    # 优先使用设备 ID
    device_id = request.headers.get("X-Device-ID")
    if device_id:
        return f"device:{device_id}"
    
    # 否则使用 IP
    return f"ip:{request.client.host}"

def check_rate_limit(request: Request, max_requests: int = 100, window_hours: int = 1):
    """检查频率限制"""
    client_id = get_client_id(request)
    count, first_request = request_counts[client_id]
    now = datetime.now()
    
    # 如果超过时间窗口，重置计数
    if now - first_request > timedelta(hours=window_hours):
        request_counts[client_id] = (1, now)
        return
    
    # 检查是否超过限制
    if count >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_hours} hour(s)"
        )
    
    # 增加计数
    request_counts[client_id] = (count + 1, first_request)
