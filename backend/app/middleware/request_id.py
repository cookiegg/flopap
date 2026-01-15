"""
Request ID 中间件 - 请求追踪
为每个请求生成唯一 ID，用于日志追踪和调试
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger
import contextvars

# 上下文变量存储 request_id
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')


def get_request_id() -> str:
    """获取当前请求 ID"""
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成或获取 request_id
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())[:8]
        
        # 设置到上下文
        request_id_var.set(request_id)
        
        # 添加到 logger
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        
        # 添加到响应头
        response.headers['X-Request-ID'] = request_id
        return response
