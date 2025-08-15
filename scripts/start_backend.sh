#!/bin/bash
# 启动后端服务脚本

echo "🚀 启动后端服务..."

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(dirname "$(dirname "$0")")"
BACKEND_DIR="$PROJECT_ROOT/minio-file-manager/backend"

# 切换到后端目录
cd "$BACKEND_DIR" || exit 1

echo "📂 工作目录: $BACKEND_DIR"

# 检查是否有进程占用9011端口
if lsof -Pi :9011 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口9011已被占用，正在停止原有服务..."
    lsof -Pi :9011 -sTCP:LISTEN -t | xargs kill -9
    sleep 2
fi

# 检查虚拟环境或依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到requirements.txt文件"
    exit 1
fi

# 启动后端服务
echo "✅ 在端口9011启动后端服务..."
echo "📝 API文档地址: http://localhost:9011/docs"
echo "📝 按 Ctrl+C 停止服务"
echo "-" * 60

python3 -m uvicorn app.main:app --reload --port 9011 --host 0.0.0.0

# 如果需要后台运行，取消下面的注释并注释上面的行
# nohup python3 -m uvicorn app.main:app --reload --port 9011 --host 0.0.0.0 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
# echo "✅ 后端服务已在后台启动"
# echo "📝 查看日志: tail -f $PROJECT_ROOT/logs/backend.log"
