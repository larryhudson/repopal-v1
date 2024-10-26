from flask import Flask, render_template
from flask_session import Session
from repopal.api import api
import os

app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    SESSION_TYPE='filesystem',
    GITHUB_CLIENT_ID=os.environ.get('GITHUB_CLIENT_ID'),
    GITHUB_CLIENT_SECRET=os.environ.get('GITHUB_CLIENT_SECRET'),
    GITHUB_APP_ID=os.environ.get('GITHUB_APP_ID')
)

# Initialize Flask-Session
Session(app)

# Initialize SQLAlchemy
from repopal.models import db
db.init_app(app)

# Register the API blueprint
app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
