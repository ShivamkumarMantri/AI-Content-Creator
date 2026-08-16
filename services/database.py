"""
VortexAI Database Storage Service Abstraction.
Supports:
1. Local Development & Testing: SQLite database (embedded, zero-configuration).
2. Production / Vercel Serverless: Hosted PostgreSQL (Neon, Supabase, Vercel Postgres, AWS RDS, Railway)
   via DATABASE_URL / POSTGRES_URL environment variables with automatic schema provisioning.
"""

import os
import json
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# ==========================================================================
# Abstract Database Store Interface
# ==========================================================================

class BaseDatabaseStore(ABC):
    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def get_all_projects(self, search: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_project(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        pass

    @abstractmethod
    def get_dashboard_stats(self) -> Dict[str, Any]:
        pass


# ==========================================================================
# 1. Local SQLite Implementation
# ==========================================================================

class SQLiteDatabaseStore(BaseDatabaseStore):
    def __init__(self, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = db_path
        else:
            from services.video import get_storage_dir
            self.db_path = get_storage_dir() / "vortex_studio.db"
        self.init_db()

    def _get_connection(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                style TEXT DEFAULT 'cinematic',
                platform TEXT DEFAULT 'Instagram Reels',
                duration INTEGER DEFAULT 30,
                status TEXT DEFAULT 'completed',
                hook TEXT,
                script TEXT,
                scenes_json TEXT,
                video_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if d.get("scenes_json"):
            try:
                d["scenes"] = json.loads(d["scenes_json"])
            except Exception:
                d["scenes"] = []
        else:
            d["scenes"] = []
        return d

    def get_all_projects(self, search: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM projects"
        params = []
        conditions = []

        if search and search.strip():
            s = f"%{search.strip()}%"
            conditions.append("(title LIKE ? OR topic LIKE ? OR hook LIKE ?)")
            params.extend([s, s, s])

        if platform and platform.strip() and platform != "all":
            conditions.append("platform = ?")
            params.append(platform.strip())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        project_id = data.get("id")
        scenes = data.get("scenes", [])
        scenes_json = json.dumps(scenes) if isinstance(scenes, list) else (data.get("scenes_json") or "[]")

        cursor.execute("""
            INSERT OR REPLACE INTO projects (
                id, title, topic, style, platform, duration, status,
                hook, script, scenes_json, video_url, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            data.get("title", "Untitled Project"),
            data.get("topic", ""),
            data.get("style", "cinematic"),
            data.get("platform", "Instagram Reels"),
            int(data.get("duration", 30)),
            data.get("status", "completed"),
            data.get("hook", ""),
            data.get("script", ""),
            scenes_json,
            data.get("video_url", ""),
            data.get("created_at", now),
            now
        ))
        conn.commit()
        conn.close()
        return self.get_project_by_id(project_id)

    def update_project(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_project_by_id(project_id)
        if not existing:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        scenes = data.get("scenes", existing.get("scenes", []))
        scenes_json = json.dumps(scenes) if isinstance(scenes, list) else existing.get("scenes_json", "[]")

        cursor.execute("""
            UPDATE projects SET
                title = ?,
                topic = ?,
                style = ?,
                platform = ?,
                duration = ?,
                status = ?,
                hook = ?,
                script = ?,
                scenes_json = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            data.get("title", existing["title"]),
            data.get("topic", existing["topic"]),
            data.get("style", existing["style"]),
            data.get("platform", existing["platform"]),
            int(data.get("duration", existing["duration"])),
            data.get("status", existing["status"]),
            data.get("hook", existing["hook"]),
            data.get("script", existing["script"]),
            scenes_json,
            now,
            project_id
        ))
        conn.commit()
        conn.close()
        return self.get_project_by_id(project_id)

    def delete_project(self, project_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_dashboard_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM projects")
        total_projects = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as completed FROM projects WHERE status = 'completed'")
        completed_videos = cursor.fetchone()["completed"]

        cursor.execute("SELECT SUM(duration) as total_dur FROM projects WHERE status = 'completed'")
        row_dur = cursor.fetchone()["total_dur"]
        total_seconds = row_dur if row_dur is not None else 0

        cursor.execute("SELECT platform, COUNT(*) as count FROM projects GROUP BY platform")
        platform_rows = cursor.fetchall()
        platforms = {r["platform"]: r["count"] for r in platform_rows}

        conn.close()
        return {
            "total_projects": total_projects,
            "completed_videos": completed_videos,
            "total_duration_seconds": total_seconds,
            "platform_breakdown": platforms,
            "database_driver": "sqlite"
        }


# ==========================================================================
# 2. Production PostgreSQL Implementation (Neon, Supabase, Vercel Postgres)
# ==========================================================================

class PostgreSQLDatabaseStore(BaseDatabaseStore):
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.init_db()

    def _get_connection(self):
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            return conn
        except ImportError:
            # Fallback for environments using psycopg (v3)
            import psycopg
            from psycopg.rows import dict_row
            conn = psycopg.connect(self.db_url, row_factory=dict_row)
            return conn

    def init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(64) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                topic TEXT NOT NULL,
                style VARCHAR(64) DEFAULT 'cinematic',
                platform VARCHAR(64) DEFAULT 'Instagram Reels',
                duration INTEGER DEFAULT 30,
                status VARCHAR(64) DEFAULT 'completed',
                hook TEXT,
                script TEXT,
                scenes_json TEXT,
                video_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def _format_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        d = dict(row)
        if d.get("scenes_json"):
            try:
                d["scenes"] = json.loads(d["scenes_json"])
            except Exception:
                d["scenes"] = []
        else:
            d["scenes"] = []
        # Format timestamps to readable strings
        if d.get("created_at") and not isinstance(d["created_at"], str):
            d["created_at"] = str(d["created_at"])[:19]
        if d.get("updated_at") and not isinstance(d["updated_at"], str):
            d["updated_at"] = str(d["updated_at"])[:19]
        return d

    def get_all_projects(self, search: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM projects"
        params = []
        conditions = []

        if search and search.strip():
            s = f"%{search.strip()}%"
            conditions.append("(title ILIKE %s OR topic ILIKE %s OR hook ILIKE %s)")
            params.extend([s, s, s])

        if platform and platform.strip() and platform != "all":
            conditions.append("platform = %s")
            params.append(platform.strip())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [self._format_row(r) for r in rows]

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return self._format_row(row) if row else None

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        project_id = data.get("id")
        scenes = data.get("scenes", [])
        scenes_json = json.dumps(scenes) if isinstance(scenes, list) else (data.get("scenes_json") or "[]")

        cursor.execute("""
            INSERT INTO projects (
                id, title, topic, style, platform, duration, status,
                hook, script, scenes_json, video_url, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                topic = EXCLUDED.topic,
                style = EXCLUDED.style,
                platform = EXCLUDED.platform,
                duration = EXCLUDED.duration,
                status = EXCLUDED.status,
                hook = EXCLUDED.hook,
                script = EXCLUDED.script,
                scenes_json = EXCLUDED.scenes_json,
                video_url = EXCLUDED.video_url,
                updated_at = EXCLUDED.updated_at
        """, (
            project_id,
            data.get("title", "Untitled Project"),
            data.get("topic", ""),
            data.get("style", "cinematic"),
            data.get("platform", "Instagram Reels"),
            int(data.get("duration", 30)),
            data.get("status", "completed"),
            data.get("hook", ""),
            data.get("script", ""),
            scenes_json,
            data.get("video_url", ""),
            data.get("created_at", now),
            now
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return self.get_project_by_id(project_id)

    def update_project(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_project_by_id(project_id)
        if not existing:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        scenes = data.get("scenes", existing.get("scenes", []))
        scenes_json = json.dumps(scenes) if isinstance(scenes, list) else existing.get("scenes_json", "[]")

        cursor.execute("""
            UPDATE projects SET
                title = %s,
                topic = %s,
                style = %s,
                platform = %s,
                duration = %s,
                status = %s,
                hook = %s,
                script = %s,
                scenes_json = %s,
                updated_at = %s
            WHERE id = %s
        """, (
            data.get("title", existing["title"]),
            data.get("topic", existing["topic"]),
            data.get("style", existing["style"]),
            data.get("platform", existing["platform"]),
            int(data.get("duration", existing["duration"])),
            data.get("status", existing["status"]),
            data.get("hook", existing["hook"]),
            data.get("script", existing["script"]),
            scenes_json,
            now,
            project_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return self.get_project_by_id(project_id)

    def delete_project(self, project_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return deleted

    def get_dashboard_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM projects")
        total_projects = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as completed FROM projects WHERE status = 'completed'")
        completed_videos = cursor.fetchone()["completed"]

        cursor.execute("SELECT COALESCE(SUM(duration), 0) as total_dur FROM projects WHERE status = 'completed'")
        total_seconds = cursor.fetchone()["total_dur"]

        cursor.execute("SELECT platform, COUNT(*) as count FROM projects GROUP BY platform")
        platform_rows = cursor.fetchall()
        platforms = {r["platform"]: r["count"] for r in platform_rows}

        cursor.close()
        conn.close()
        return {
            "total_projects": total_projects,
            "completed_videos": completed_videos,
            "total_duration_seconds": total_seconds,
            "platform_breakdown": platforms,
            "database_driver": "postgresql"
        }


# ==========================================================================
# Database Factory & Module API
# ==========================================================================

_store_instance: Optional[BaseDatabaseStore] = None

def get_db_store() -> BaseDatabaseStore:
    """
    Factory that initializes the appropriate database store:
    - PostgreSQL: If DATABASE_URL or POSTGRES_URL environment variable is provided.
    - SQLite: Default for local development, tests, and fallback.
    """
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if db_url:
        try:
            _store_instance = PostgreSQLDatabaseStore(db_url)
            return _store_instance
        except Exception as exc:
            # Fall back to SQLite if PostgreSQL fails to initialize
            print(f"[Database Warning] Failed to connect to PostgreSQL ({exc}). Falling back to SQLite.")
            _store_instance = SQLiteDatabaseStore()
            return _store_instance

    _store_instance = SQLiteDatabaseStore()
    return _store_instance

# Module-Level Convenience Functions (Preserves 100% Backwards Compatibility)

def init_db():
    get_db_store().init_db()

def get_all_projects(search: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
    return get_db_store().get_all_projects(search=search, platform=platform)

def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    return get_db_store().get_project_by_id(project_id)

def create_project(data: Dict[str, Any]) -> Dict[str, Any]:
    return get_db_store().create_project(data)

def update_project(project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return get_db_store().update_project(project_id, data)

def delete_project(project_id: str) -> bool:
    return get_db_store().delete_project(project_id)

def get_dashboard_stats() -> Dict[str, Any]:
    return get_db_store().get_dashboard_stats()
