# Flopap 单机版 - 用户快速开始指南

> 自托管学术论文发现平台，单用户版本

## 系统要求

- **操作系统**: Linux / macOS / Windows (需安装 Docker)
- **内存**: 4GB 以上
- **硬盘**: 20GB 以上可用空间
- **必需软件**: Docker + Docker Compose

## 快速开始（3 步）

### 步骤 1：安装 Docker

**Linux (Ubuntu/Debian)**:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

**macOS/Windows**:

- 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 步骤 2：部署 Flopap

```bash
# 下载项目
git clone https://github.com/your-username/flopap.git
cd flopap
git checkout feat/standalone-edition

# 配置环境变量 (添加 API Keys)
cp .env.standalone.example .env
nano .env  # 或使用其他编辑器

# 必填配置：
# DEEPSEEK_API_KEY_01=sk-your-deepseek-key  (翻译/解读)
# DASHSCOPE_API_KEY=sk-your-dashscope-key   (向量搜索)
```

**获取 API Keys**:

- DeepSeek: <https://platform.deepseek.com/> (需注册)
- Dashscope: <https://dashscope.aliyuncs.com/> (需注册)

```bash
# 启动服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 步骤 3：访问应用

**网页版**: 打开浏览器访问 `http://localhost:8000`

**移动端** (可选):

1. 获取电脑IP地址: `ip addr | grep inet`
2. 手机连接同一WiFi
3. 浏览器访问: `http://192.168.x.x:8000`

## 使用说明

### 自动内容生成

系统每天凌晨 4:00 自动执行：

- 从 arXiv 抓取最新 AI/ML/NLP/CV 论文
- 生成中文翻译
- 生成 AI 解读
- 生成语音朗读

**首次使用**: 手动触发内容生成

```bash
docker exec flopap-app python -c "from app.scripts.run_factory_mode import job_daily_refresh; job_daily_refresh()"
```

预计时间：10-30分钟（取决于论文数量和网络速度）

### 功能介绍

- **📰 论文流**: 浏览每日推荐论文
- **🔖 收藏**: 点击书签图标收藏论文
- **👍 点赞**: 告诉系统你喜欢的论文类型
- **🎧 语音播放**: 听论文中文朗读
- **🌐 翻译**: 查看论文的中文翻译
- **🤖 AI解读**: 查看AI生成的论文解读

## 常见问题

**Q: 为什么没有论文显示？**
A: 首次使用需要等待内容生成完成（见"首次使用"部分）

**Q: 如何停止服务？**

```bash
docker-compose down
```

**Q: 如何更新到最新版本？**

```bash
git pull origin feat/standalone-edition
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Q: 数据存储在哪里？**
A: 所有数据保存在 `./data` 目录：

- `data/pg/` - 数据库
- `data/tts_opus/` - 语音文件

**Q: API Key 费用多少？**
A:

- DeepSeek: 约 ¥0.001/千tokens (非常便宜)
- Dashscope: 有免费额度

每天处理100篇论文，预计费用 < ¥5/月

**Q: 可以修改抓取的论文类别吗？**
A: 编辑 `.env` 文件中的 `ARXIV_QUERY` 参数

## 卸载

```bash
# 停止并删除容器
docker-compose down

# 删除数据（可选）
rm -rf data/

# 删除项目
cd ..
rm -rf flopap/
```

## 技术支持

遇到问题？请在 GitHub 提交 Issue: <https://github.com/your-username/flopap/issues>
