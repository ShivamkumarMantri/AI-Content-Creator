from flask import Flask, render_template, request, jsonify, send_from_directory
from services.ai import generate_content_plan
from services.video import create_video, VideoRenderingService, get_storage_dir
from services.database import (
    get_all_projects,
    get_project_by_id,
    create_project,
    update_project,
    delete_project,
    get_dashboard_stats
)
from pathlib import Path
import json, uuid, time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

@app.get("/api/stats")
def get_stats():
    return jsonify(get_dashboard_stats())

@app.post("/api/generate-plan")
def generate_plan():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    style = (data.get("style") or "cinematic").strip()
    duration = int(data.get("duration") or 30)
    platform = (data.get("platform") or "Instagram Reels").strip()
    api_key = (data.get("api_key") or "").strip() or None
    model = (data.get("model") or "").strip() or None

    if not topic:
        return jsonify({"error": "Please enter a topic."}), 400

    try:
        plan = generate_content_plan(
            topic=topic,
            style=style,
            duration=duration,
            platform=platform,
            api_key=api_key,
            model=model
        )
        return jsonify(plan)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

@app.post("/api/create-video")
def make_video():
    data = request.get_json(silent=True) or {}
    scenes = data.get("scenes", [])
    title = (data.get("title") or "AI Video").strip()
    topic = (data.get("topic") or title).strip()
    hook = data.get("hook", "")
    script = data.get("script", "")
    style = data.get("style", "cinematic")
    platform = data.get("platform", "Instagram Reels")
    
    # Audio & Captions options
    enable_voiceover = bool(data.get("enable_voiceover", True))
    voice = data.get("voice", "male_deep")
    enable_music = bool(data.get("enable_music", True))
    enable_captions = bool(data.get("enable_captions", True))
    caption_style = data.get("caption_style", "hormozi")
    caption_position = data.get("caption_position", "bottom")
    api_key = (data.get("api_key") or "").strip() or None

    duration = sum(int(s.get("duration", 5)) for s in scenes) if scenes else 30

    if not scenes:
        return jsonify({"error": "Generate a content plan first."}), 400

    try:
        storage = get_storage_dir()
        job_id = data.get("id") or uuid.uuid4().hex
        output = storage / f"{job_id}.mp4"
        
        render_result = VideoRenderingService.render(
            scenes=scenes,
            title=title,
            output=output,
            style=style,
            platform=platform,
            enable_voiceover=enable_voiceover,
            voice=voice,
            enable_music=enable_music,
            enable_captions=enable_captions,
            caption_style=caption_style,
            caption_position=caption_position,
            api_key=api_key
        )
        
        video_url = render_result.get("video_url") or f"/generated/{output.name}"
        
        project_data = {
            "id": job_id,
            "title": title,
            "topic": topic,
            "hook": hook,
            "script": script,
            "style": style,
            "platform": platform,
            "duration": duration,
            "status": "completed",
            "video_url": video_url,
            "scenes": scenes
        }
        saved_project = create_project(project_data)
        
        return jsonify({
            "video_url": video_url,
            "project": saved_project,
            "render_report": render_result
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

# ==========================================================================
# REST API: Project Management (SQLite CRUD)
# ==========================================================================

@app.get("/api/projects")
def list_projects():
    search = request.args.get("search")
    platform = request.args.get("platform")
    projects = get_all_projects(search=search, platform=platform)
    return jsonify(projects)

@app.post("/api/projects")
def add_project():
    data = request.get_json(silent=True) or {}
    if not data.get("title") and not data.get("topic"):
        return jsonify({"error": "Title or topic is required."}), 400
    
    if not data.get("id"):
        data["id"] = uuid.uuid4().hex
        
    created = create_project(data)
    return jsonify(created), 201

@app.get("/api/projects/<project_id>")
def get_project(project_id):
    project = get_project_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found."}), 404
    return jsonify(project)

@app.put("/api/projects/<project_id>")
def edit_project(project_id):
    data = request.get_json(silent=True) or {}
    updated = update_project(project_id, data)
    if not updated:
        return jsonify({"error": "Project not found or update failed."}), 404
    return jsonify(updated)

@app.delete("/api/projects/<project_id>")
def remove_project(project_id):
    deleted = delete_project(project_id)
    # Remove associated video file if it exists
    storage = get_storage_dir()
    target_file = storage / f"{project_id}.mp4"
    if target_file.exists():
        try:
            target_file.unlink()
        except Exception:
            pass
    return jsonify({"success": deleted})

@app.get("/generated/<path:filename>")
def generated(filename):
    storage = get_storage_dir()
    return send_from_directory(storage, filename, as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True)
