#!/bin/bash
# 快速切换环境配置

case "$1" in
  local)
    echo "VITE_REMOTE_API_URL=http://localhost:8000" > .env
    echo "✅ 切换到本地环境 (localhost:8000)"
    ;;
  cloud)
    echo "VITE_REMOTE_API_URL=http://118.178.93.186" > .env
    echo "✅ 切换到云服务器 (118.178.93.186)"
    ;;
  *)
    echo "用法: $0 {local|cloud}"
    echo ""
    echo "  local  - 本地开发 (localhost:8000)"
    echo "  cloud  - 云服务器 (118.178.93.186)"
    exit 1
    ;;
esac

echo ""
echo "当前配置:"
cat .env
echo ""
echo "运行以下命令重新构建:"
echo "  npm run build && npx cap sync android"
