import requests

BASE_URL = "http://127.0.0.1:5000"
TOKEN = None


def set_token(token):
    global TOKEN
    TOKEN = token


def get_headers():
    """Возвращает заголовки с токеном авторизации, если он установлен."""
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = TOKEN
    return headers


def register_user(name, password):
    """Регистрация нового пользователя."""
    url = f"{BASE_URL}/user"
    json = {"name": name, "password": password}
    response = requests.post(url, json=json, headers=get_headers())
    if response.status_code == 200:
        print("User registered:", response.json())
    else:
        print("Error:", response.json())


def login_user(name, password):
    """Авторизация пользователя."""
    url = f"{BASE_URL}/login"
    payload = {"name": name, "password": password}
    response = requests.post(url, json=payload, headers=get_headers())
    if response.status_code == 200:
        token = response.json().get("token")
        set_token(token)  # Устанавливаем токен для использования в других запросах
        print("Logged in as:", name)
    else:
        print("Error:", response.json())


# Advertisement Functions
def create_ad(title, description):
    """Создать объявление."""
    url = f"{BASE_URL}/ads"
    json = {"title": title, "description": description}
    response = requests.post(url, json=json, headers=get_headers())
    if response.status_code == 201:
        print("Ad created:", response.json())
    else:
        print("Error:", response.json())


def get_ads():
    """Получить список всех объявлений."""
    url = f"{BASE_URL}/ads"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        ads = response.json()
        print("Ads:", ads)
    else:
        print("Error:", response.json())


def get_ad(ad_id):
    """Получить объявление по ID."""
    url = f"{BASE_URL}/ads/{ad_id}"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        print("Ad details:", response.json())
    else:
        print("Error:", response.json())


def update_ad(ad_id, title=None, description=None):
    """Обновить объявление."""
    url = f"{BASE_URL}/ads/{ad_id}"
    json = {}
    if title:
        json["title"] = title
    if description:
        json["description"] = description
    response = requests.patch(url, json=json, headers=get_headers())
    if response.status_code == 200:
        print("Ad updated:", response.json())
    else:
        print("Error:", response.json())


def delete_ad(ad_id):
    """Удалить объявление."""
    url = f"{BASE_URL}/ads/{ad_id}"
    response = requests.delete(url, headers=get_headers())
    if response.status_code == 200:
        print("Ad deleted:", response.json())
    else:
        print("Error:", response.json())


if __name__ == "__main__":
    # url = f"{BASE_URL}/login"
    # json = {"name": "test_user", "password": "securepassword"}
    # response = requests.post(url, json=json, headers=get_headers())
    # print(response.json())
    register_user("test_user", "securepassword")
    login_user("test_user", "securepassword")
    print(TOKEN)

    create_ad("Ad 1", "Description for ad 1")
    create_ad("Ad 2", "Description for ad 2")

    get_ads()

    get_ad(2)

    update_ad(2, title="Updated Ad 1")

    delete_ad(1)

    get_ads()