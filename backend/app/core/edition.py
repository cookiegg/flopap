"""Edition configuration for FloPap"""
from enum import Enum


class Edition(str, Enum):
    COMMUNITY = "community"  # 开源版本，用户自己部署
    CLOUD = "cloud"  # 云服务版本，需要 OAuth


# 功能开关
FEATURES = {
    Edition.COMMUNITY: {
        "oauth_required": False,
        "shared_ai_content": False,  # 不共享 AI 生成内容
        "user_isolation": False,  # 单用户模式
    },
    Edition.CLOUD: {
        "oauth_required": True,
        "shared_ai_content": True,  # 共享 AI 生成内容
        "user_isolation": True,  # 多用户隔离
    }
}


def get_current_edition() -> Edition:
    """获取当前版本"""
    from app.core.config import settings
    return settings.edition


def get_feature(feature_name: str) -> bool:
    """获取当前版本的功能开关"""
    return FEATURES[get_current_edition()].get(feature_name, False)


def is_cloud_edition() -> bool:
    """是否为云服务版本"""
    return get_current_edition() == Edition.CLOUD


def is_community_edition() -> bool:
    """是否为开源版本"""
    return get_current_edition() == Edition.COMMUNITY
