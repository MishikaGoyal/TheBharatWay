from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import users_collection
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']

    if users_collection.find_one({'email': email}):
        return jsonify({"message": "User already exists"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = {'name': name, 'email': email, 'password': hashed}
    users_collection.insert_one(user)

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    user = users_collection.find_one({'email': email})
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user['_id']))
    return jsonify({
        "token": token,
        "user": {
            "id": str(user['_id']),
            "name": user['name'],
            "email": user['email']
        }
    })
