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
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SESSION_TYPE="filesystem",
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///repopal.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GITHUB_CLIENT_ID=os.environ.get("GITHUB_CLIENT_ID"),
        GITHUB_CLIENT_SECRET=os.environ.get("GITHUB_CLIENT_SECRET"),
        GITHUB_APP_ID=os.environ.get("GITHUB_APP_ID"),
        GITHUB_APP_NAME=os.environ.get("GITHUB_APP_NAME"),
    )

    # Initialize Flask-Session
    Session(app)

    # Initialize SQLAlchemy
    from repopal.models import db

    db.init_app(app)

    # Register the API blueprint
    app.register_blueprint(api, url_prefix="/api")

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
