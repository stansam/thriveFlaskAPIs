from flask import Flask, jsonify
from typing import Any
from sqlalchemy import text

def _register_health_check(app: Flask) -> None:
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        """Shallow health check — verifies DB connectivity."""      
        status: dict[str, Any] = {"status": "ok", "db": "ok", "storage": "ok"}
        http_code = 200

        try:
            from app.models.base import db
            db.session.execute(text("SELECT 1"))
        except Exception as exc:
            status["status"] = "degraded"
            status["db"]     = f"error: {exc}"
            http_code = 503

        return jsonify(status), http_code