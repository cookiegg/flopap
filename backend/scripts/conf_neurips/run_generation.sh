#!/bin/bash
# NeurIPS 2025 推荐池快速生成脚本

set -e

echo "🚀 NeurIPS 2025 推荐池批量生成"
echo "================================"

# 进入项目目录
cd "$(dirname "$0")/../.."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未找到，请确保Python已安装"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --dry-run        试运行，只显示统计信息"
    echo "  --test           测试模式，只处理2个用户"
    echo "  --force          强制更新已存在的排序表"
    echo "  --all            为所有用户生成（默认）"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --dry-run     # 查看统计信息"
    echo "  $0 --test        # 测试运行"
    echo "  $0 --all         # 正式运行"
    echo "  $0 --force       # 强制更新所有"
}

# 解析参数
case "${1:-}" in
    --dry-run)
        echo "📊 试运行模式 - 查看统计信息"
        python scripts/conf_neurips/generate_neurips_pools.py --dry-run
        ;;
    --test)
        echo "🧪 测试模式 - 处理2个用户"
        python scripts/conf_neurips/generate_neurips_pools.py --max-users 2
        ;;
    --force)
        echo "🔄 强制更新模式 - 更新所有用户"
        read -p "⚠️  这将重新生成所有用户的排序表，确认继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python scripts/conf_neurips/generate_neurips_pools.py --force
        else
            echo "❌ 已取消"
            exit 1
        fi
        ;;
    --all|"")
        echo "🎯 正式运行 - 为所有用户生成推荐池"
        python scripts/conf_neurips/generate_neurips_pools.py
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        echo "❌ 未知选项: $1"
        show_help
        exit 1
        ;;
esac

echo ""
echo "✅ 完成！查看日志文件获取详细信息"
echo "📁 结果文件位于: scripts/conf_neurips/temp_results/"
