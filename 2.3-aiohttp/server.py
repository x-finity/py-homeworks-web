from aiohttp import web
from models import init_orm, close_orm, Session, User, Advertisement
import json
from sqlalchemy.exc import IntegrityError
from bcrypt import hashpw, checkpw, gensalt
from functools import wraps
from sqlalchemy.future import select

app = web.Application()

def hash_password(password: str):
    password = password.encode()
    hashed_password_bytes = hashpw(password, gensalt())
    hashed_password = hashed_password_bytes.decode()
    return hashed_password

def check_password(password: str, hashed_password: str) -> bool:
    password = password.encode()
    hashed_password = hashed_password.encode()
    return checkpw(password, hashed_password)

async def orm_context(app: web.Application):
    print("START")
    await init_orm()
    yield
    await close_orm()
    print("FINISH")

@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        result = await handler(request)
        return result

app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)

def get_http_error(error, message):
    message = json.dumps({"error": message})
    error = error(text=message, content_type='application/json')
    raise error

async def get_user_by_id(user_id: int, session: Session):
    user = await session.get(User, user_id)
    if user is None:
        raise get_http_error(web.HTTPNotFound, "User not found")
    return user

async def add_user(user: User, session: Session):
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise get_http_error(web.HTTPConflict, "User already exists")

async def delete_user(user: User, session: Session):
    await session.delete(user)
    await session.commit()

async def get_ad_by_id(ad_id: int, session: Session):
    if ad_id is None:
        ads = await session.execute(select(Advertisement))
        ads = ads.scalars().all()
    else:
        ads = await session.get(Advertisement, ad_id)
    if ads is None:
        raise get_http_error(web.HTTPNotFound, "Advertisement not found")
    return ads

async def add_ad(ad: Advertisement, session: Session):
    session.add(ad)
    await session.commit()


class UserView(web.View):

    @property
    def user_id(self) -> int:
        return int(self.request.match_info['user_id'])

    @property
    def session(self):
        return self.request.session

    async def get(self):
        user = await get_user_by_id(self.user_id, self.session)
        return web.json_response(user.to_dict)

    async def post(self):
        json_data = await self.request.json()
        json_data['password'] = hash_password(json_data['password'])
        user = User(**json_data)
        await add_user(user, self.session)
        return web.json_response(user.dict_id)

    async def patch(self):
        user = await get_user_by_id(self.user_id, self.session)
        json_data = await self.request.json()
        if 'password' in json_data:
            json_data['password'] = hash_password(json_data['password'])
        for key, value in json_data.items():
            setattr(user, key, value)
        await add_user(user, self.session)
        return web.json_response(user.dict_id)

    async def delete(self):
        user = await get_user_by_id(self.user_id, self.session)
        await delete_user(user, self.session)
        return web.json_response({"status": "success"})


def login_required(func):
    @wraps(func)
    async def wrapper(request: web.Request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise get_http_error(web.HTTPUnauthorized, "Unauthorized, no auth header")
        token = auth_header
        if not token:
            raise get_http_error(web.HTTPUnauthorized, "Unauthorized")
        try:
            user = await get_user_by_id(token, request.session)
        except ValueError:
            raise get_http_error(web.HTTPUnauthorized, "Unauthorized, invalid token")
        if not user:
            raise get_http_error(web.HTTPUnauthorized, "Unauthorized, no such user")
        request.session['user_id'] = user.id
        return await func(request, *args, **kwargs)
    return wrapper

class AdvertisementView(web.View):

    @property
    def ad_id(self):
        try:
            return int(self.request.match_info['ad_id'])
        except KeyError:
            return None

    @property
    def session(self):
        return self.request.session

    async def get(self):
        ads = await get_ad_by_id(self.ad_id, self.session)
        return web.json_response([ad.to_dict for ad in ads])

    # @login_required
    async def post(self):
        json_data = await self.request.json()
        ad = Advertisement(**json_data, owner_id=int(self.request.headers.get('Authorization')))
                           # owner_id=self.session['user_id'])
                           # owner_id=int(self.request.headers.get('Authorization')))
        await add_ad(ad, self.session)
        return web.json_response(ad.dict_id)

    async def patch(self):
        ad = await get_ad_by_id(self.ad_id, self.session)
        print(ad, type(ad))
        json_data = await self.request.json()
        for key, value in json_data.items():
            setattr(ad, key, value)
        await add_ad(ad, self.session)
        return web.json_response(ad.dict_id)

    async def delete(self):
        ad = await get_ad_by_id(self.ad_id, self.session)
        await delete_user(ad, self.session)
        return web.json_response({"status": f"ad {self.ad_id} deleted successfully"})



app.add_routes([
    web.post("/user", UserView),
    web.get("/user/{user_id:\d+}", UserView),
    web.patch("/user/{user_id:\d+}", UserView),
    web.delete("/user/{user_id:\d+}", UserView),
    web.post("/ad", AdvertisementView),
    web.get("/ad", AdvertisementView),
    web.get("/ad/{ad_id:\d+}", AdvertisementView),
    web.patch("/ad/{ad_id:\d+}", AdvertisementView),
    web.delete("/ad/{ad_id:\d+}", AdvertisementView)
])

if __name__ == "__main__":
    web.run_app(app)
