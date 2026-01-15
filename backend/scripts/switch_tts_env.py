#!/usr/bin/env python3
"""
TTS环境切换脚本
快速在本地和云端模式之间切换
"""

import os
import sys

def switch_to_local():
    """切换到本地模式"""
    print("🏠 切换到本地模式...")
    os.environ['TTS_ENVIRONMENT'] = 'local'
    
    # 更新.env文件
    update_env_file('TTS_ENVIRONMENT', 'local')
    
    print("✅ 已切换到本地模式")
    print("📁 文件路径: /data/proj/flopap/data/tts_opus")
    print("🔗 访问URL: http://localhost:8000/static/tts/")

def switch_to_cloud():
    """切换到云端模式"""
    print("☁️  切换到云端模式...")
    os.environ['TTS_ENVIRONMENT'] = 'production'
    
    # 更新.env文件
    update_env_file('TTS_ENVIRONMENT', 'production')
    
    print("✅ 已切换到云端模式")
    print("📁 文件路径: COS tts/tts_opus/")
    print("🔗 访问URL: https://cdn.flopap.com/tts/tts_opus/")

def update_env_file(key, value):
    """更新.env文件"""
    env_file = '/data/proj/flopap/backend/.env'
    
    if not os.path.exists(env_file):
        print(f"⚠️  .env文件不存在，创建新文件")
        with open(env_file, 'w') as f:
            f.write(f"{key}={value}\n")
        return
    
    # 读取现有内容
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # 更新或添加配置
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            updated = True
            break
    
    if not updated:
        lines.append(f"{key}={value}\n")
    
    # 写回文件
    with open(env_file, 'w') as f:
        f.writelines(lines)

def show_status():
    """显示当前状态"""
    current_env = os.getenv('TTS_ENVIRONMENT', 'local')
    
    print("📊 当前TTS配置状态")
    print("=" * 30)
    print(f"🎯 环境模式: {current_env}")
    
    if current_env == 'local':
        print("📁 文件源: 本地文件系统")
        print("🔗 基础URL: http://localhost:8000/static/tts/")
        print("📂 本地目录: /data/proj/flopap/data/tts_opus")
    else:
        print("📁 文件源: 腾讯云COS")
        print("🔗 基础URL: https://cdn.flopap.com/tts/tts_opus/")
        print("🔐 签名验证: 启用")

def main():
    if len(sys.argv) < 2:
        print("🎵 TTS环境切换工具")
        print("=" * 30)
        print("使用方法:")
        print("  python3 switch_tts_env.py local    # 切换到本地模式")
        print("  python3 switch_tts_env.py cloud    # 切换到云端模式") 
        print("  python3 switch_tts_env.py status   # 查看当前状态")
        print("")
        show_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'local':
        switch_to_local()
    elif command in ['cloud', 'production']:
        switch_to_cloud()
    elif command == 'status':
        show_status()
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: local, cloud, status")

if __name__ == '__main__':
    main()
