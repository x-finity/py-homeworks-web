import requests
import json

def get_hero(person_id):
    response = requests.get(f'https://swapi.py4e.com/api/people/{person_id}').json()
    return response

def extract_info(data):
    return json.loads(data)

if __name__ == '__main__':
    data = get_hero(1)
    print(data)
    print(type(data))
    # print(extract_info(data))