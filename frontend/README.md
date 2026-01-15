# FloPap Frontend

React + TypeScript + Vite frontend application for FloPap paper recommendation system.

## Directory Structure

```
frontend/
├── src/                    # Source code
│   ├── components/         # React components
│   ├── services/          # API and business logic services
│   ├── hooks/             # Custom React hooks
│   ├── assets/            # Static assets (images, icons)
│   └── public/            # Public static files
├── docs/                  # Documentation
├── scripts/               # Build and utility scripts
├── logs/                  # Build and runtime logs
├── build-configs/         # Build configuration files
├── android/               # Android Capacitor build
├── dist/                  # Production build output
└── node_modules/          # Dependencies
```

## Environment Files

- `.env` - Current environment (symlink)
- `.env.development` - Development configuration
- `.env.production` - Production configuration
- `.env.android` - Android build configuration
- `.env.mobile` - Mobile app configuration
- `.env.example` - Environment template

## Quick Start

```bash
npm install
npm run dev
```

## Build Commands

```bash
npm run build          # Production build
npm run build:android  # Android build
npm run preview        # Preview production build
```

For detailed documentation, see `docs/` directory.
