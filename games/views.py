from django.shortcuts import render
import requests
from datetime import date

def game_listing(requests):
    return
#testing
auth_token = "26af8e03-7266-4878-a6ce-6890a733f7d5"
headers = {"Authorization": auth_token}
today = "2026-06-13"
params = {
    "cursor": 0,
    "per_page": 100,
    "dates[]": today,
    
}
response = requests.get("https://api.balldontlie.io/v1/games", headers = headers, params = params)

data = response.json()
print(f"Found {len(data['data'])} games for {today}:\n")

for game in data["data"]:












