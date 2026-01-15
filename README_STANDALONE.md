# Flopap Standalone Edition

> **Self-hosted, single-user academic paper discovery platform**

## Overview

Flopap Standalone Edition is a simplified, self-contained version designed for individual researchers. It removes all cloud dependencies and authentication requirements.

## Features

✅ **No Authentication Required**: Single-user mode, instant access  
✅ **Fully Local**: All data stored on your machine  
✅ **Automated Content Generation**: Daily paper fetching, AI translation, and TTS audio  
✅ **Zero Cloud Dependencies**: No Tencent COS, no Alibaba SMS, no OAuth  
✅ **Simple Deployment**: 2 Docker containers via docker-compose  

## Requirements

- **Hardware**: 4GB RAM minimum, 8GB recommended
- **Software**: Docker & Docker Compose
- **API Keys**:
  - DeepSeek API (for AI translation/interpretation): <https://platform.deepseek.com/>
  - Dashscope API (for embeddings): <https://dashscope.aliyuncs.com/>

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-username/flopap.git
cd flopap
git checkout feat/standalone-edition

# Copy environment template
cp .env.standalone.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Start Services

```bash
docker-compose up -d
```

This will start 2 services:

- `flopap-db`: PostgreSQL database
- `flopap-app`: All-in-one app (Backend API + Frontend + Worker)

### 3. Access Flopap

Open your browser to: **<http://localhost:8000>**

You'll be automatically logged in as "Local User" (no login screen).

## Configuration

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `ARXIV_SUBMISSION_DELAY_DAYS` | How many days back to fetch papers | `3` |
| `ARXIV_MAX_RESULTS` | Maximum papers to fetch | `10000` |
| `ARXIV_QUERY` | arXiv category filter | `cat:cs.AI OR cat:cs.LG...` |
| `DEEPSEEK_API_KEY_01` | DeepSeek API key (required) | - |
| `DASHSCOPE_API_KEY` | Dashscope API key (required) | - |

## Content Generation

The worker thread runs daily at **04:00 local time** to:

1. Fetch new papers from arXiv
2. Generate Chinese translations (DeepSeek)
3. Generate AI interpretations (DeepSeek)
4. Generate TTS audio (Edge-TTS)

**Manual trigger** (for testing):

```bash
docker exec flopap-app python -c "from app.scripts.run_factory_mode import job_daily_refresh; job_daily_refresh()"
```

## Data Storage

All data is stored in the `./data` directory:

```
data/
├── pg/                # PostgreSQL database files
└── tts_opus/          # TTS audio files (.opus)
```

## Mobile App Deployment

### Prerequisites

- Android Studio (for Android app)
- Node.js installed
- Server running on same WiFi network or accessible via internet

### Steps

1. **Get Server IP Address**

```bash
# On the server machine
ip addr show | grep inet
# Look for your local IP (e.g., 192.168.1.100)
```

1. **Configure Mobile App**

```bash
cd frontend

# Copy standalone config
cp .env.standalone .env

# Edit .env and replace IP address
nano .env
# Change: VITE_API_URL=http://YOUR_SERVER_IP:8000/api
```

1. **Build and Run**

```bash
# Build frontend
npm install
npm run build

# Sync to Android
npx cap sync android

# Open in Android Studio
npx cap open android
```

1. **Run on Device**

- Connect Android device or start emulator
- Ensure device is on same WiFi network as server
- Click Run in Android Studio

### Network Configuration

**Local Network (Same WiFi)**:

- Server: `http://192.168.x.x:8000`
- Mobile connects directly via local IP
- No internet required after paper download

**Public Internet (Cloud Server)**:

- Server: `http://YOUR_PUBLIC_IP:8000`
- Open port 8000 in firewall/security group
- Mobile can connect from anywhere

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs -f app

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### No papers showing up

1. Wait for initial content generation
2. Check logs: `docker-compose logs -f app`
3. Manually trigger fetch: See "Content Generation" section above

### TTS audio not playing

- Ensure `data/tts_opus/` directory exists
- Check worker thread logs in app container

## Architecture

```
┌─────────────────┐
│  Web Browser    │
└────────┬────────┘
         │ http://localhost:8000
         │
┌────────▼─────────────┐
│  All-in-One App      │
│  ┌─────────────────┐ │
│  │ FastAPI Backend │ │
│  │ Static Frontend │ │
│  │ Worker Thread   │ │
│  └─────────────────┘ │
└──────────┬───────────┘
           │
    ┌──────▼──────┐
    │ PostgreSQL  │
    └─────────────┘
```

## Differences from Cloud Edition

| Feature | Cloud Edition | Standalone Edition |
|---------|--------------|-------------------|
| Authentication | OAuth/SMS | None (auto-login) |
| Storage | Tencent COS | Local filesystem |
| Users | Multi-user | Single default user |
| Redis | Required | Removed |
| Deployment | 5 containers | 2 containers |

## License

[Your License Here]

## Support

For issues, please open a GitHub issue.
