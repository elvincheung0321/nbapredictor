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
    home = game["home_team"]
    away = game["visitor_team"]
    score = f"{game['visitor_team_score']}-{game['home_team_score']}"
    print(f"{away['abbreviation']} @ {home['abbreviation']}: {score} ({game['status']})")

print(data["data"])







