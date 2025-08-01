from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from auth import auth_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

# JWT config
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET")
jwt = JWTManager(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")

@app.route('/')
def home():
    return {"message": "Welcome to The Bharat Way (Flask version)"}

if __name__ == "__main__":
    app.run(port=8000, debug=True)
