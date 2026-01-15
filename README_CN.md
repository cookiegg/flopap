<div align="center">
  <img src="frontend/src/assets/logo.png" width="120" alt="FloPap Logo" />
  <h1>FloPap</h1>
  <p><strong>重塑科研阅读体验。像刷抖音一样刷论文。</strong></p>

  <p>
    <a href="https://flopap.com" target="_blank">
      <img src="https://img.shields.io/badge/在线演示-flopap.com-blue?style=for-the-badge&logo=google-chrome" alt="Live Demo" />
    </a>
    <a href="https://github.com/cookiegg/flopap/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/开源协议-MIT-green?style=for-the-badge" alt="License" />
    </a>
    <a href="https://github.com/cookiegg/flopap/releases">
      <img src="https://img.shields.io/github/v/release/cookiegg/flopap?style=for-the-badge&color=orange" alt="Release" />
    </a>
  </p>

  <p>
    <a href="README_CN.md">🇨🇳 中文文档</a> | 
    <a href="README.md">🇬🇧 English</a>
  </p>
</div>

---

## 🚀 简介

**FloPap** 是一款开创性的学术论文阅读应用。受到 TikTok (抖音) 沉浸式信息流的启发，我们为科研人员打造了一个高效、轻松的 **ArXiv** 与 **顶会** (NeurIPS, CVPR, ICLR) 论文阅读平台。

利用碎片化时间保持科研嗅觉，通过 AI 辅助快速获取核心观点，享受移动优先的极致阅读体验。

### ✨ 核心特性

- **📱 沉浸式信息流**: 像刷短视频一样浏览论文，上下滑动切换。
- **⚡ AI 智能辅助**: 自动生成 TL;DR 摘要、核心创新点总结及多语言翻译。
- **🎧 听论文模式**: 高质量 TTS 语音朗读，通勤路上也能"读"论文。
- **☁️ 全平台支持**: Web、iOS、Android (PWA/Native) 无缝切换。
- **🎨 极致 UI 设计**: 采用 Glassmorphism 玻璃拟态设计，流畅的交互动画，支持深色模式。

---

### 📱 移动端体验

即刻访问 [flopap.com](https://flopap.com) 体验完整交互。

<div align="center">
  <img src="frontend/public/landing-phone.gif" width="300" alt="FloPap Live UI" style="border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
</div>

### 核心流程

1.  **全球科研数据源**: 聚合 ArXiv (每日更新) 以及顶级 AI 会议 (NeurIPS, CVPR, ICLR) 的最新论文。
2.  **AI 内容引擎**:
    *   **智能摘要**: 生成精炼的 TL;DR 和核心观点。
    *   **多语言翻译**: 消除语言障碍，提供精准的学术翻译。
    *   **语音合成**: 将论文内容转化为自然流畅的音频，支持听书模式。
3.  **视觉体验**: 以 TikTok 风格的竖屏信息流呈现，配合智能图表和清晰的排版。

---

## 📦 快速开始

### 方案 A: Docker 一键部署 (推荐) 🐳

最简单的部署方式，只需安装 **Docker**。

1. **克隆仓库**
   ```bash
   git clone https://github.com/cookiegg/flopap.git
   cd flopap
   ```

2. **配置环境变量**
   在根目录创建 `.env` 文件并填写必要的 API Key：
   ```env
   # AI 功能需要配置
   DEEPSEEK_API_KEY=your_key_here
   DASHSCOPE_API_KEY=your_key_here
   ```

3. **启动服务**
   ```bash
   docker compose up -d
   ```
   *(注：旧版 Docker 用户请使用 `docker-compose up -d`)*
   启动后访问 `http://localhost:8000` 即可开始阅读！

### 方案 B: 手动安装 (开发模式)

需要 Node.js >= 18, Python >= 3.11, PostgreSQL 和 Redis 环境。

1. **前端**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **后端**
   ```bash
   cd backend
   pip install -r requirements.txt
   # 需配置本地 .env文件中的 DATABASE_URL
   python -m app.main
   ```

---

## 🤝 参与贡献

非常欢迎提交 Issue 或 Pull Request！

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 开源协议

本项目基于 MIT 协议开源。详见 `LICENSE` 文件。

<div align="center">
  <p>Built with ❤️ by <a href="https://github.com/cookiegg">CookieGG</a></p>
</div>
