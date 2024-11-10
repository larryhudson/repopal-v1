import os

from dotenv import load_dotenv
from flask import Flask, render_template

from flask_session import Session
from repopal.api import api


def create_app():
    """Application factory function"""
    load_dotenv()  # Load environment variables from .env

    app = Flask(__name__)

    # Configuration
    # Database configuration
    db_url = os.environ.get("DATABASE_URL", "sqlite:///repopal.db")
    app.logger.info(f"Configuring database with URL: {db_url}")

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SESSION_TYPE="filesystem",
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,  # Enable SQL query logging
        GITHUB_CLIENT_ID=os.environ.get("GITHUB_CLIENT_ID"),
        GITHUB_CLIENT_SECRET=os.environ.get("GITHUB_CLIENT_SECRET"),
        GITHUB_WEBHOOK_SECRET=os.environ.get("GITHUB_WEBHOOK_SECRET"),
        GITHUB_APP_ID=os.environ.get("GITHUB_APP_ID"),
        GITHUB_APP_NAME=os.environ.get("GITHUB_APP_NAME"),
    )

    # Initialize Flask-Session
    Session(app)

    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO)


    # Initialize extensions
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    from repopal.extensions import db

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379/0",
        default_limits=["1000 per hour"],
        strategy="fixed-window",
    )

    # Register blueprints
    app.register_blueprint(api, url_prefix="/api")

    # Import and register webhooks blueprint
    from repopal.api.routes.webhooks import init_webhook_handlers, webhooks_bp
    app.register_blueprint(webhooks_bp, url_prefix="/api")
    init_webhook_handlers(app)

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
