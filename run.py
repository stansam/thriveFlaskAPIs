from app import create_app

app = create_app()

if __name__ == "__main__":
    from app.core.config import settings
    app.run(
        host="0.0.0.0",
        port=int(__import__("os").getenv("PORT", 5000)),
        debug=settings.DEBUG,
        use_reloader=settings.DEBUG,
    )