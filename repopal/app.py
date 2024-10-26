from flask import Flask
from repopal.api import api

app = Flask(__name__)

# Register the API blueprint
app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def hello():
    return 'Welcome to RepoPal!'

if __name__ == '__main__':
    app.run(debug=True)
