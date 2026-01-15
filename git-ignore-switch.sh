#!/bin/bash
# Git忽略管理脚本

case "$1" in
    "local")
        echo "切换到本地开发模式 - 忽略测试和开发文件"
        cp .gitignore.local .gitignore
        ;;
    "remote")
        echo "切换到远程提交模式 - 包含测试和开发文件"
        cp .gitignore.remote .gitignore
        ;;
    "status")
        echo "当前忽略状态:"
        if cmp -s .gitignore .gitignore.local; then
            echo "本地开发模式 (忽略测试文件)"
        elif cmp -s .gitignore .gitignore.remote; then
            echo "远程提交模式 (包含测试文件)"
        else
            echo "自定义模式"
        fi
        ;;
    *)
        echo "用法: $0 {local|remote|status}"
        echo "  local  - 本地开发模式 (忽略测试文件)"
        echo "  remote - 远程提交模式 (包含测试文件)"
        echo "  status - 查看当前模式"
        exit 1
        ;;
esac
