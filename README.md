# ⚡ VortexAI Studio — Automated Short-Form Video Content Creator

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Production-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://aivideocontentcreator.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Ready-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](#license)

> 🚀 **Production Application is Live on Vercel!**

### 🌐 Live Production Links
* **Primary Production URL**: [https://aivideocontentcreator.vercel.app](https://aivideocontentcreator.vercel.app/)
* **Deployment URL**: [https://aivideocontentcreator-vsgggv6v3-gen-ai-83de.vercel.app](https://aivideocontentcreator-vsgggv6v3-gen-ai-83de.vercel.app/)
* **Vercel Project Dashboard**: [https://vercel.com/gen-ai-83de/ai_video_content_creator](https://vercel.com/gen-ai-83de/ai_video_content_creator)

---

**VortexAI Studio** is a full-stack, automated AI video generation and project management platform. It transforms raw text prompts and creative ideas into structured multi-scene scripts, styled motion graphics, animated karaoke-style captions, neural voiceovers, procedural background music, and master-grade **1080 × 1920 (9:16) vertical MP4 videos** ready for **Instagram Reels, TikTok, YouTube Shorts, and LinkedIn**.

---

## 🎬 System Architecture

```text
                                  +---------------------------+
                                  |    Web UI / Studio App    |
                                  | (HTML5, Vanilla CSS & JS) |
                                  +-------------+-------------+
                                                |
                                    REST API (Flask / JSON)
                                                |
                                                v
+---------------------------------------------------------------------------------------------------+
|                                   Flask Application Core (app.py)                                 |
+---------------------+-------------------------+-------------------------+-------------------------+
                      |                         |                         |
                      v                         v                         v
        +---------------------------+  +------------------+  +-------------------------+
        |   AI Content Generator    |  |  SQLite Database |  |  Audio Synthesis Engine |
        |     (services/ai.py)      |  |  (database.py)   |  |    (services/audio.py)  |
        |  - OpenAI GPT-4o / Mini   |  |  - CRUD Projects |  |  - Neural Edge-TTS      |
        |  - Local Fallback Engine  |  |  - Search & Stats|  |  - Ambient Synth Music  |
        |  - Platform-Aware Hook    |  |  - Scene Storage |  |  - FFmpeg Audio Ducking |
        +-------------+-------------+  +------------------+  +------------+------------+
                      |                                                   |
                      +-------------------------+-------------------------+
                                                |
                                                v
                               +----------------------------------+
                               |     Video Rendering Engine       |
                               |      (services/video.py)         |
                               |  - Pillow 1080x1920 Canvas       |
                               |  - Animated Captions (captions.py|
                               |  - Ken Burns Zoom/Pan Effects    |
                               |  - FFmpeg H.264/yuv420p 30 FPS   |
                               +----------------+-----------------+
                                                |
                                                v
                               +----------------------------------+
                               |   Master Vertical MP4 Output     |
                               | (Instant Browser Stream Preview) |
                               +----------------------------------+
```

---

## 🚀 Key Features

### 1. 🧠 Platform-Aware Generative AI Planning
* Generates structured JSON production plans containing **Title**, **Retention Hook**, **Voiceover Script**, **Scene Breakdown**, **Visual Directives**, and **On-Screen Typography**.
* Supports **Instagram Reels**, **TikTok**, **YouTube Shorts**, and **LinkedIn**.
* Powered by OpenAI Structured JSON mode with an intelligent **Local Fallback Engine** that generates platform-specific pacing and CTAs when no API key is provided.

### 2. 🎨 Motion Graphics & Video Generation
* Compiles **1080 × 1920 (9:16 Full HD)** master videos at **30 FPS**.
* Generates custom gradient meshes, cyber grids, ambient glow orbs, and glassmorphic title cards tailored to visual styles (*Cinematic*, *Technology*, *Minimal Modern*, *Social Energetic*).
* Smooth **Ken Burns camera motion** (alternating dynamic zoom and pan across scenes) with seamless **fade transitions**.
* Web-ready encoding (`H.264`, `yuv420p`, `+faststart`).

### 3. 💬 Animated Karaoke-Style Captions
* Word-by-word active keyword highlighting powered by [`services/captions.py`](services/captions.py).
* Preset visual styles:
  * **Hormozi**: Bold yellow/green pop highlight with heavy black outline.
  * **Cyber Neon**: Cyan glow text with translucent dark container.
  * **Minimal Clean**: Crisp white typography on frosted glass badge.
  * **Gold Luxury**: Warm golden typography with drop shadow.
* Configurable screen positioning: `Bottom (75%)`, `Center (50%)`, `Top (25%)`.

### 4. 🎙️ AI Voiceover & Procedural Music
* **Neural Text-to-Speech**: Multiple voice persona presets (Deep Male, Clear Female, Energetic Male, Expressive Female).
* **Procedural Ambient Music**: Synthesizes smooth electronic chord progressions in Python without external audio assets.
* **Audio Ducking**: FFmpeg `amix` dynamically lowers background music volume under spoken dialogue.

### 5. 🗄️ Full SQLite Project Management
* Persistent storage in `generated/vortex_studio.db` using [`services/database.py`](services/database.py).
* Full CRUD capabilities: Create, Read, Update/Edit, and Delete projects with automated disk cleanup.
* Search and filter by title, topic, hook, platform, and status (`Completed`, `Draft`, `Planned`).
* Real-time dashboard analytics (Total Projects, Completed Count, Total Duration).

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & APIs** | Python 3.11+, Flask, SQLite3, `python-dotenv` |
| **Video & Graphics** | FFmpeg, `imageio-ffmpeg`, Pillow (PIL), `libx264` |
| **Audio & Speech** | `edge-tts` (Microsoft Neural Voices), Python `wave` & `struct`, OpenAI TTS |
| **AI Reasoning** | OpenAI API (GPT-4o / GPT-4o-mini), Local Fallback Generative Engine |
| **Frontend UI** | HTML5, Vanilla CSS (Design Tokens, Glassmorphism, Dark Mode), Vanilla JavaScript (ES6+) |

---

## 📦 Installation & Setup

### 1. Clone or Open the Repository
```bash
cd ai_video_content_creator
```

### 2. Create and Activate Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note on FFmpeg:** The project includes `imageio-ffmpeg` to automatically resolve the FFmpeg binary on Windows/macOS/Linux. A separate system install is optional.

### 4. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` if you wish to use your own OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```
*(If no API key is provided, the application automatically uses the built-in local engine).*

### 5. Start the Application
```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the main single-page application UI |
| `GET` | `/api/stats` | Fetches aggregated dashboard metrics from SQLite |
| `POST` | `/api/generate-plan` | Generates structured JSON scene breakdown from topic |
| `POST` | `/api/create-video` | Compiles 1080x1920 MP4 with audio/captions & saves to SQLite |
| `GET` | `/api/projects` | Lists all projects with optional `?search=` and `?platform=` |
| `POST` | `/api/projects` | Creates a new draft or planned project |
| `GET` | `/api/projects/<id>` | Retrieves project details and parsed scene objects |
| `PUT` | `/api/projects/<id>` | Updates project title, topic, platform, status, or script |
| `DELETE` | `/api/projects/<id>` | Deletes project from SQLite and cleans up MP4 file |
| `GET` | `/generated/<path>` | Serves generated MP4 video files |

---

## 🗄️ Database Storage Architecture (Local vs Production)

VortexAI Studio employs a clean **Database Storage Abstraction** (`services/database.py`):

1. **Local Development (Default - Zero Configuration)**:
   * Uses an embedded SQLite database stored dynamically in `generated/vortex_studio.db`.
   * Requires no external services or connection URLs.

2. **Production / Vercel Serverless (PostgreSQL)**:
   * Set the `DATABASE_URL` or `POSTGRES_URL` environment variable to connect to any hosted PostgreSQL database (e.g., **Neon**, **Supabase**, **Vercel Postgres**, **AWS RDS**, or **Railway**).
   * Schema tables are automatically initialized on startup with index optimizations and timestamp management.

```env
# Example Production PostgreSQL Connection String
DATABASE_URL=postgresql://neondb_owner:password@ep-sample-123.us-east-2.aws.neon.tech/neondb?sslmode=require
```

---

## 🧪 Testing & Verification

Run automated API, database, and video rendering tests:
```powershell
# 1. Test AI Planning & Fallback
.venv\Scripts\python.exe -c "from services.ai import generate_content_plan; print(generate_content_plan('3 Productivity Hacks', 'cinematic', 15, 'TikTok')['title'])"

# 2. Test Database Abstraction & Dashboard Stats
.venv\Scripts\python.exe -c "from services.database import get_dashboard_stats; print(get_dashboard_stats())"
```

---

## 📄 License
MIT License. Built for portfolio demonstration and automated content engineering.
