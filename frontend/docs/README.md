# Flopap 前端

React + Vite + Tailwind 构建的 PWA 前端，用于提供 TikTok 式刷论文体验。

## 快速开始

```bash
pnpm install # 或 npm install / yarn install
pnpm run dev
```

- 开发服务器默认端口：`5173`
- 通过 Vite 代理将 `/api` 请求转发到 `http://localhost:8000`

## 构建与预览

```bash
pnpm run build
pnpm run preview
```

## 主要功能

- 垂直刷卡式论文浏览，支持点赞、收藏、不感兴趣（含二次确认）
- 本地状态实时更新，与后端推荐池联动
- 用户主页展示收藏、点赞、不感兴趣列表
- PWA 支持：可安装到桌面，离线缓存关键资源

## 目录结构

- `src/api`：后端接口封装
- `src/hooks`：数据加载与状态管理
- `src/pages`：路由页面
- `src/components`：UI 组件
- `src/state/router.tsx`：React Router 配置

如需自定义主题或图标，可替换 `public/icons` 中的 PNG 文件并更新 `manifest.webmanifest`。
