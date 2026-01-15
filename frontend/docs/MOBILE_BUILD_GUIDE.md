# FloPap 移动端构建指南

## 📱 环境配置系统

### 🔧 可用的环境配置文件

| 文件 | 用途 | API URL |
|------|------|---------|
| `.env` | 默认配置 | `http://localhost:8000/api` |
| `.env.development` | 开发环境 | `http://localhost:8000/api` |
| `.env.production` | 生产环境 | `https://flopap.com/api` |
| `.env.mobile` | 移动端模拟器 | `http://10.0.2.2:8000/api` |
| `.env.android` | Android真机 | `http://192.168.45.26:8000/api` |

### 🚀 构建命令

#### Web构建
```bash
# 开发环境构建
npm run build:dev

# 生产环境构建  
npm run build:prod

# 默认构建
npm run build
```

#### 移动端构建
```bash
# 开发环境 + 同步到移动端
npm run cap:sync:dev

# 生产环境 + 同步到移动端
npm run cap:sync:prod

# 默认构建 + 同步
npm run cap:sync
```

#### 移动端开发
```bash
# 打开Android Studio
npm run cap:open:android

# 打开iOS Xcode
npm run cap:open:ios

# 仅复制文件到移动端
npm run cap:copy
```

## 🌐 API URL配置逻辑

### 自动检测逻辑
```typescript
export const getApiBaseUrl = () => {
  if (Capacitor.isNativePlatform()) {
    // 移动端原生应用：使用环境变量
    return import.meta.env.VITE_API_URL || 'https://flopap.com/api';
  }
  // Web端：使用相对路径（通过代理）
  return '/api';
};
```

### 环境变量优先级
1. **移动端**: `VITE_API_URL` 环境变量
2. **Web端**: 相对路径 `/api` (通过Nginx代理)
3. **回退**: `https://flopap.com/api`

## 🔄 快速环境切换

### 使用switch_env.sh脚本
```bash
# 切换到本地开发
./switch_env.sh local

# 切换到云服务器
./switch_env.sh cloud
```

### 手动切换环境
```bash
# 复制对应的环境配置
cp .env.development .env    # 开发环境
cp .env.production .env     # 生产环境
cp .env.mobile .env         # 移动端模拟器
cp .env.android .env        # Android真机
```

## 📱 移动端部署流程

### Android开发流程
```bash
# 1. 构建前端（选择环境）
npm run build:dev          # 开发环境
# 或
npm run build:prod         # 生产环境

# 2. 同步到Android项目
npx cap sync android

# 3. 打开Android Studio
npx cap open android

# 4. 在Android Studio中构建和运行
```

### 一键部署命令
```bash
# 开发环境一键部署
npm run cap:sync:dev && npx cap open android

# 生产环境一键部署  
npm run cap:sync:prod && npx cap open android
```

## 🔧 Capacitor配置

### 应用配置
- **App ID**: `com.flopap.app`
- **App Name**: `FloPap`
- **Web目录**: `dist`

### 插件配置
- **Google OAuth**: 已配置客户端ID
- **启动屏幕**: 2秒自动隐藏
- **HTTP**: 支持明文传输（开发环境）

## 🌍 不同环境的使用场景

### 开发环境 (development)
- **用途**: 本地开发和测试
- **API**: `http://localhost:8000/api`
- **构建**: `npm run build:dev`
- **特点**: 热重载、调试信息

### 生产环境 (production)
- **用途**: 正式发布
- **API**: `https://flopap.com/api`
- **构建**: `npm run build:prod`
- **特点**: 代码压缩、性能优化

### 移动端环境 (mobile)
- **用途**: Android模拟器测试
- **API**: `http://10.0.2.2:8000/api`
- **特点**: 模拟器专用IP地址

### Android真机环境 (android)
- **用途**: Android真机测试
- **API**: `http://192.168.45.26:8000/api`
- **特点**: 局域网IP地址

## 🚨 常见问题

### 1. API连接失败
```bash
# 检查当前环境配置
cat .env

# 检查后端服务状态
curl http://localhost:8000/api/docs

# 重新构建并同步
npm run build:dev && npx cap sync
```

### 2. Android构建失败
```bash
# 清理并重新构建
rm -rf android/app/build
npm run build:prod
npx cap sync android
```

### 3. 环境变量不生效
```bash
# 确保重新构建
npm run build:dev  # 或 build:prod
npx cap sync android
```

## 📊 构建验证

### 检查构建结果
```bash
# 检查API URL是否正确
grep -r "localhost:8000" dist/    # 开发环境
grep -r "flopap.com" dist/        # 生产环境

# 检查构建文件
ls -la dist/
```

### 移动端测试
```bash
# 在Android Studio中检查
# 1. 打开 android/app/src/main/assets/public/
# 2. 检查构建文件是否更新
# 3. 运行应用并检查网络请求
```

## 🎯 推荐工作流程

### 日常开发
```bash
# 1. 开发环境构建和测试
npm run dev                    # Web开发服务器
npm run cap:sync:dev          # 移动端同步

# 2. 在Android Studio中测试移动端
npx cap open android
```

### 发布准备
```bash
# 1. 生产环境构建
npm run build:prod

# 2. 移动端发布构建
npm run cap:sync:prod
npx cap open android

# 3. 在Android Studio中生成APK/AAB
```

---

**Framework V2特性**: 所有环境都支持新的API密钥管理、内容生成和推荐设置功能！
