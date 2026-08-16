# Production & Vercel Deployment Architecture Guide

This document outlines the architecture for deploying **VortexAI Studio** in production, serverless environments (e.g., **Vercel**, **AWS Lambda**), and local development.

---

## 1. Architecture Overview: Local vs Serverless Cloud

| Component | Local Development (`localhost`) | Serverless / Cloud Production (**Vercel**) |
| :--- | :--- | :--- |
| **Execution Environment** | Persistent Python runtime | Ephemeral Serverless Functions (read-only root) |
| **Filesystem / Storage** | Persistent local disk (`generated/`) | Ephemeral `/tmp` storage (or Cloud Object Storage / S3 / R2 / Vercel Blob) |
| **Video Rendering Engine** | High-performance Python + Pillow + FFmpeg | Service Abstraction: Local FFmpeg or Serverless Fallback / Cloud Rendering Hook |
| **Database** | SQLite embedded (`generated/vortex_studio.db`) | SQLite in `/tmp` (or remote PostgreSQL / Supabase / Neon) |
| **AI Content Planning** | OpenAI API + Deterministic Offline Fallback | OpenAI API + Deterministic Offline Fallback |
| **Audio Voiceover** | Edge-TTS / Procedural Audio Synthesis | Edge-TTS / Procedural Audio / Pre-rendered Audio |

---

## 2. Video Rendering Service Abstraction (`services/video.py`)

The video rendering pipeline is decoupled from the web request handlers using the **`VideoRenderingService`** abstraction:

```text
                                  ┌────────────────────────┐
                                  │   Flask Web Handler    │
                                  │  (POST /create-video)  │
                                  └───────────┬────────────┘
                                              │
                              ┌───────────────▼───────────────┐
                              │     VideoRenderingService     │
                              │      (services/video.py)      │
                              └───────┬───────────────┬───────┘
                                      │               │
                     [FFmpeg Available]               [Serverless / Cloud Restricted]
                                      │               │
                                      ▼               ▼
                       ┌──────────────────────┐ ┌──────────────────────┐
                       │  LocalFFmpegRenderer │ │ ServerlessCloudQueue │
                       │                      │ │                      │
                       │ • 1080x1920 30FPS    │ │ • Ephemeral /tmp Post│
                       │ • Ken Burns Pan/Zoom │ │ • Audio Synthesis    │
                       │ • Animated Captions  │ │ • Scene Asset Bundle │
                       │ • Audio Ducking      │ │ • Webhook Dispatch   │
                       └──────────────────────┘ └──────────────────────┘
```

### Strategy 1: Full Local / Containerized Pipeline
* Uses Pillow to generate 1080x1920 graphical scenes.
* Uses FFmpeg filtergraphs for smooth Ken Burns zoom/pan camera motion, crossfades, and H.264 MP4 encoding.
* Uses `edge-tts` and procedural harmonic audio synthesis for voiceovers and background music.

### Strategy 2: Serverless / Vercel Safe Mode
* Automatically routes temporary output to `/tmp/vortex_generated`.
* Generates high-resolution scene assets and audio narration packages.
* In environments where long-running FFmpeg child processes exceed serverless execution budgets (e.g. 10s timeout), it returns a serverless-safe media package without crashing the Lambda function.

---

## 3. Production Scaling: Cloud Rendering Worker Pattern

For high-volume production deployments with video rendering queues:

1. **Web Layer (Vercel)**:
   * Handles user authentication, dashboard management, and AI prompt scripting.
   * Dispatches video rendering jobs to an asynchronous queue (e.g., AWS SQS, Upstash QStash, or Celery).

2. **Rendering Worker (Modal / Render / AWS ECS / Creatomate)**:
   * Dedicated background container with full hardware-accelerated FFmpeg and GPU rendering.
   * Renders the master 1080x1920 MP4 and uploads to S3 / Cloudflare R2 / Vercel Blob.
   * Sends a webhook notification back to update project status to `completed`.

---

## 4. Vercel Configuration Setup

1. **Deploy Repository to Vercel**:
   * Framework Preset: **Other** / **Flask**
   * Output Directory: `.`
2. **Set Environment Variables in Vercel Dashboard**:
   * `OPENAI_API_KEY`: *(Optional)* Your OpenAI API Key for GPT-4o scripting.
   * `OPENAI_MODEL`: *(Optional)* `gpt-4o-mini` (default)
   * `SERVERLESS`: `1`
3. **Deploy**:
   * Vercel will automatically build and run the serverless function.
