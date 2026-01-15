# Frontend 目录结构说明

## 📁 新的目录结构

```
frontend/
├── src/                    # 源代码目录（原 tikpaper_frontend）
│   ├── App.tsx            # 主应用组件
│   ├── index.tsx          # 入口文件
│   ├── types.ts           # TypeScript 类型定义
│   ├── constants.ts       # 常量定义
│   ├── components/        # React 组件
│   ├── services/          # API 服务
│   │   ├── backendService.ts    # 后端 API 调用
│   │   ├── conferenceService.ts # 会议数据服务
│   │   └── storageService.ts    # 本地存储服务
│   └── public/            # 静态资源
├── android/               # Android 项目（Capacitor）
├── dist/                  # 构建输出目录
├── index.html             # HTML 入口
├── package.json           # 项目配置
├── vite.config.ts         # Vite 配置
├── tailwind.config.js     # Tailwind CSS 配置
├── tsconfig.json          # TypeScript 配置
├── capacitor.config.ts    # Capacitor 配置
└── .env                   # 环境变量

frontend_backup_YYYYMMDD_HHMMSS/  # 旧版本备份
```

## 🔄 变更说明

### 之前的结构
```
frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── state/
│   ├── styles/
│   ├── tikpaper_frontend/  # 实际使用的代码
│   └── main.tsx
```

### 现在的结构
```
frontend/
├── src/                    # 直接使用原 tikpaper_frontend 的内容
│   ├── App.tsx
│   ├── components/
│   ├── services/
│   └── ...
```

## ✅ 优点

1. **结构清晰**: 不再有嵌套的 `tikpaper_frontend` 目录
2. **统一代码**: Web 端和 Android 端使用同一套代码
3. **易于维护**: 配置文件都在根目录，一目了然
4. **标准结构**: 符合 Vite + React 项目的标准结构

## 🚀 使用方法

### 开发模式（Web）
```bash
cd /data/proj/papertik/frontend
npm run dev
# 访问 http://localhost:5173
```

### 构建生产版本
```bash
npm run build
# 输出到 dist/ 目录
```

### Android 开发
```bash
# 构建并同步到 Android
npm run build
npx cap sync

# 打开 Android Studio
npx cap open android
```

## 📝 配置文件说明

### vite.config.ts
- 简化的 Vite 配置
- 监听所有网络接口（0.0.0.0）
- 端口 5173

### capacitor.config.ts
- Capacitor 配置
- 指定 webDir 为 'dist'
- Android 和 iOS 配置

### .env
- 环境变量配置
- `VITE_REMOTE_API_URL`: 后端 API 地址

## 🔧 关键文件

### src/services/backendService.ts
- 后端 API 调用
- 当前配置: `http://192.168.45.26:8000/api`
- 支持通过环境变量 `VITE_REMOTE_API_URL` 覆盖

### src/App.tsx
- 主应用组件
- 包含数据源切换逻辑（arXiv ↔ NeurIPS）
- 处理用户交互和状态管理

## 📦 依赖说明

主要依赖：
- `react` + `react-dom`: UI 框架
- `vite`: 构建工具
- `@capacitor/core`: 跨平台框架
- `lucide-react`: 图标库
- `axios`: HTTP 客户端
- `tailwindcss`: CSS 框架

## 🗂️ 备份说明

旧的 frontend 目录已备份到：
```
frontend_backup_YYYYMMDD_HHMMSS/
```

如需恢复旧版本：
```bash
cd /data/proj/papertik
rm -rf frontend
mv frontend_backup_YYYYMMDD_HHMMSS frontend
```

## ⚠️ 注意事项

1. **不要**直接修改 `dist/` 目录的内容（会被构建覆盖）
2. **不要**提交 `node_modules/` 到版本控制
3. **记得**在修改代码后运行 `npm run build` 和 `npx cap sync` 来更新 Android 应用
4. **记得**更新 `.env` 文件中的 API 地址（如果 IP 变化）
