"""
短信服务 - 手机验证码发送和验证
功能：
- 阿里云短信服务集成
- 验证码生成和发送
- 验证码验证和过期管理
- 手机号格式验证
- 防刷机制和频率限制
- 支持手机号登录流程
"""
import time
import logging
from typing import Dict, Optional
from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self, access_key_id: str, access_key_secret: str):
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = 'dypnsapi.aliyuncs.com'
        config.read_timeout = 30000  # 30秒超时
        config.connect_timeout = 10000  # 10秒连接超时
        self.client = Dypnsapi20170525Client(config)
        self._cache: Dict[str, tuple[str, float]] = {}
        self.settings = get_settings()
    
    async def send_code(self, phone_number: str) -> Dict:
        """发送验证码"""
        # 频率限制检查
        if phone_number in self._cache:
            _, last_time = self._cache[phone_number]
            if time.time() - last_time < 60:
                logger.warning(f"手机号 {phone_number} 发送过于频繁")
                return {"success": False, "message": "发送过于频繁，请稍后再试"}
        
        scheme_name = "flopap_sms"
        
        request = dypnsapi_20170525_models.SendSmsVerifyCodeRequest(
            phone_number=phone_number,
            sign_name=self.settings.sms_sign_name,
            template_code=self.settings.sms_template_code,
            scheme_name=scheme_name,
            template_param='{"code":"##code##","min":"5"}',
            code_type=1,  # 纯数字
            code_length=6,  # 6位验证码
            valid_time=300,  # 5分钟有效期
            interval=60,  # 60秒间隔
            return_verify_code=True,  # 返回验证码用于缓存
        )
        
        try:
            response = self.client.send_sms_verify_code_with_options(
                request, util_models.RuntimeOptions()
            )
            
            # 使用 to_map() 安全地访问响应属性
            body_map = response.body.to_map()
            code = body_map.get('Code')
            message = body_map.get('Message')
            
            logger.info(f"短信发送响应: Code={code}, Message={message}")
            
            if code == "OK":
                # 尝试获取验证码并缓存
                model = body_map.get('Model')
                if model and isinstance(model, dict):
                    verify_code = model.get('VerifyCode') or model.get('verify_code')
                    if verify_code:
                        self._cache[phone_number] = (verify_code, time.time())
                        logger.info(f"验证码已缓存: {phone_number}")
                
                return {"success": True, "message": "验证码发送成功"}
            else:
                logger.error(f"短信发送失败: {code} - {message}")
                return {
                    "success": False,
                    "message": message or "发送失败",
                    "code": code
                }
        except Exception as e:
            logger.error(f"短信发送异常: {str(e)}", exc_info=True)
            error_msg = str(e)
            if hasattr(e, 'message'):
                error_msg = e.message
            return {"success": False, "message": f"发送失败: {error_msg}"}
    
    async def verify_code(self, phone_number: str, code: str) -> Dict:
        """验证验证码"""
        logger.info(f"验证验证码: 手机号={phone_number}, 验证码={code}")
        
        # 必须使用与发送时相同的方案名称
        scheme_name = "flopap_sms"
        
        request = dypnsapi_20170525_models.CheckSmsVerifyCodeRequest(
            phone_number=phone_number,
            verify_code=code,
            scheme_name=scheme_name,
            # case_auth_policy: 0=验证成功后失效, 1=验证成功后不失效
        )
        
        try:
            response = self.client.check_sms_verify_code_with_options(
                request, util_models.RuntimeOptions()
            )
            
            # 使用 to_map() 安全地访问响应属性
            body_map = response.body.to_map()
            code_status = body_map.get('Code')
            message = body_map.get('Message')
            model = body_map.get('Model')
            
            logger.info(f"验证响应: Code={code_status}, Message={message}, Model={model}")
            
            if code_status == "OK" and model:
                verify_result = model.get('VerifyResult') if isinstance(model, dict) else None
                
                if verify_result == 'PASS':
                    # 验证成功，清除缓存
                    self._cache.pop(phone_number, None)
                    logger.info(f"验证成功: {phone_number}")
                    return {"success": True, "message": "验证成功"}
                elif verify_result == 'FAIL':
                    logger.warning(f"验证码错误: {phone_number}")
                    return {"success": False, "message": "验证码错误"}
                else:
                    logger.warning(f"未知验证结果: {verify_result}")
                    return {"success": False, "message": "验证失败"}
            else:
                logger.error(f"验证失败: {code_status} - {message}")
                return {
                    "success": False,
                    "message": message or "验证失败"
                }
        except Exception as e:
            logger.error(f"验证异常: {str(e)}", exc_info=True)
            error_msg = str(e)
            if hasattr(e, 'message'):
                error_msg = e.message
            
            # 检查是否是常见错误
            if "400" in error_msg or "验证失败" in error_msg:
                return {"success": False, "message": "验证码错误或已过期"}
            
            return {"success": False, "message": f"验证失败: {error_msg}"}


_sms_service: Optional[SMSService] = None


def get_sms_service() -> SMSService:
    global _sms_service
    if _sms_service is None:
        settings = get_settings()
        if not settings.alibaba_cloud_access_key_id or not settings.alibaba_cloud_access_key_secret:
            raise ValueError("阿里云 AccessKey 未配置")
        _sms_service = SMSService(
            settings.alibaba_cloud_access_key_id,
            settings.alibaba_cloud_access_key_secret
        )
    return _sms_service
