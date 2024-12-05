from flask import Flask, jsonify, request, g
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from flask_bcrypt import Bcrypt
from functools import wraps

from models import Session, User, Advertisement
from scheme import CreateUser, UpdateUser, CreateAdvertisement, UpdateAdvertisement

app = Flask("test_server")
bcrypt = Bcrypt(app)

def hash_password(password: str):
    password_bytes = password.encode()
    password_hashsed_bytes = bcrypt.generate_password_hash(password_bytes)
    password_hashsed = password_hashsed_bytes.decode()
    return password_hashsed

def check_password(password: str, password_hashsed: str) -> bool:
    password_bytes = password.encode()
    password_hashsed_bytes = password_hashsed.encode()
    return bcrypt.check_password_hash(password_hashsed_bytes, password_bytes)

def hello(some_id: int):
    json_data = request.json
    qs = request.args
    headers = request.headers
    print(f'{some_id=}')
    print(f'{json_data=}')
    print(f'{qs=}')
    print(f'{headers=}')
    response = jsonify({"hello": "world"})
    return response

class HttpError(Exception):

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def error_handler(error : HttpError):
    response = jsonify({"error": error.message})
    response.status_code = error.status_code
    return response

def validate(scheme_cls: type[CreateUser] | type[UpdateUser], json_data):
    try:
        return scheme_cls(**json_data).model_dump(exclude_unset=True)
    except ValidationError as err:
        errors = err.errors()
        for error in errors:
            error.pop("ctx", None)
        raise HttpError(400, errors)

@app.before_request
def before_request():
    session = Session()
    request.session = session

@app.after_request
def after_request(http_response):
    request.session.close()
    return http_response

def add_user(user):
    request.session.add(user)
    try:
        request.session.commit()
    except IntegrityError as err:
        raise HttpError(409, "User already exists")

def get_user_by_id(user_id) -> User:
    user = request.session.get(User, user_id)
    if user is None:
        raise HttpError(404, "User not found")
    return user

class UserView(MethodView):
    def get(self, user_id):
        user = get_user_by_id(user_id)
        return jsonify(user.to_dict)

    def post(self):
        print(f'{request.json=}')
        json_data = validate(CreateUser, request.json)
        # json_data = request.json
        print(f"Received JSON: {json_data}")
        json_data["password"] = hash_password(json_data["password"])
        user = User(**json_data)
        add_user(user)
        return jsonify(user.to_dict)

    def patch(self, user_id):
        json_data = validate(UpdateUser, request.json)
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        user = get_user_by_id(user_id)
        for key, value in json_data.items():
            setattr(user, key, value)
            add_user(user)
        return jsonify(user.to_dict)

    def delete(self, user_id):
        user = get_user_by_id(user_id)
        request.session.delete(user)
        request.session.commit()
        return jsonify({"status": "deleted"})

user_view = UserView.as_view("user")

app.add_url_rule("/user/<int:user_id>", view_func=user_view, methods=["GET", "PATCH", "DELETE"])
app.add_url_rule("/user", view_func=user_view, methods=["POST"])

def auth_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        token = request.headers.get("Authorization")
        # hashed_token = hash_password(token)
        if not token:
            raise HttpError(401, "Authorization required")
        user = request.session.query(User).filter_by(password=token).first()
        if not user:
            # print(f'{token} // {hashed_token}')
            raise HttpError(403, "Invalid token")
        g.user = user  # Save current user in global context
        return f(*args, **kwargs)
    return func

# Advertisement management
class AdvertisementView(MethodView):
    def get(self, ad_id=None):
        if ad_id is None:
            ads = request.session.query(Advertisement).all()
            return jsonify([ad.to_dict for ad in ads])
        ad = request.session.get(Advertisement, ad_id)
        if not ad:
            raise HttpError(404, "Advertisement not found")
        return jsonify(ad.to_dict)

    @auth_required
    def post(self):
        json_data = validate(CreateAdvertisement, request.json)
        ad = Advertisement(**json_data, owner_id=g.user.id)
        request.session.add(ad)
        request.session.commit()
        return jsonify(ad.to_dict), 201

    @auth_required
    def patch(self, ad_id):
        ad = request.session.get(Advertisement, ad_id)
        if not ad:
            raise HttpError(404, "Advertisement not found")
        if ad.owner_id != g.user.id:
            raise HttpError(403, "You can edit only your own advertisements")
        json_data = validate(UpdateAdvertisement, request.json)
        for key, value in json_data.items():
            setattr(ad, key, value)
        request.session.commit()
        return jsonify(ad.to_dict)

    @auth_required
    def delete(self, ad_id):
        ad = request.session.get(Advertisement, ad_id)
        if not ad:
            raise HttpError(404, "Advertisement not found")
        if ad.owner_id != g.user.id:
            raise HttpError(403, "You can delete only your own advertisements")
        request.session.delete(ad)
        request.session.commit()
        return jsonify({"status": "deleted"})

ad_view = AdvertisementView.as_view("advertisement")

app.add_url_rule("/ads", view_func=ad_view, methods=["GET", "POST"])
app.add_url_rule("/ads/<int:ad_id>", view_func=ad_view, methods=["GET", "PATCH", "DELETE"])

@app.route('/login', methods=['POST'])
def login():
    json_data = request.json
    name = json_data.get('name')
    password = json_data.get('password')

    if not name or not password:
        raise HttpError(400, "Name and password are required")

    user = request.session.query(User).filter_by(name=name).first()
    if not user or not check_password(password, user.password):
        raise HttpError(403, "Invalid credentials")

    # Используем пароль как токен для упрощения
    return jsonify({"token": user.password})
app.run()