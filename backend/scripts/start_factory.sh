#!/bin/bash

# 获取脚本所在目录的上一级目录 (backend root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "🏭 Starting Flopap Factory Mode..."
echo "📂 Backend Directory: $BACKEND_DIR"

cd "$BACKEND_DIR"

# 检查是否在 tmux/screen 中运行
if [ -z "$TMUX" ] && [ -z "$STY" ]; then
    echo "⚠️  Warning: It is recommended to run this script inside tmux or screen to keep it running in background."
    echo "   Example: tmux new -s factory"
    echo "            ./scripts/start_factory.sh"
    read -p "   Press Enter to continue anyway or Ctrl+C to abort..."
fi

# 激活虚拟环境
if [ -n "$PYTHON_INTERPRETER" ]; then
    echo "🐍 Using configured interpreter: $PYTHON_INTERPRETER"
    # Ensure it's in path or just activated contextually if needed
    if [[ "$PYTHON_INTERPRETER" == *"/bin/python"* ]]; then
        # Try to source the activate script relative to interpreter
        ENV_BIN_DIR=$(dirname "$PYTHON_INTERPRETER")
        ACTIVATE_SCRIPT="$ENV_BIN_DIR/activate"
        if [ -f "$ACTIVATE_SCRIPT" ]; then
             echo "   Sourcing $ACTIVATE_SCRIPT"
             source "$ACTIVATE_SCRIPT"
        fi
    fi
elif [ -d "$BACKEND_DIR/.venv" ]; then
    echo "🐍 Activating virtual environment (.venv)..."
    source "$BACKEND_DIR/.venv/bin/activate"
elif which conda >/dev/null 2>&1; then
    # Try to detect conda environment from name or prefix
    CONDA_ENV_NAME="flopap"
    if conda info --envs | grep -q "$CONDA_ENV_NAME"; then
        echo "🐍 Activating conda environment: $CONDA_ENV_NAME"
        # Source conda.sh to ensure 'conda activate' works in script
        CONDA_BASE=$(conda info --base)
        if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
            source "$CONDA_BASE/etc/profile.d/conda.sh"
            conda activate "$CONDA_ENV_NAME"
        else
            # Fallback for some installations
            source activate "$CONDA_ENV_NAME"
        fi
    fi
fi

# 设置 PYTHONPATH
export PYTHONPATH="$BACKEND_DIR"

# 运行工厂模式脚本
python scripts/run_factory_mode.py
