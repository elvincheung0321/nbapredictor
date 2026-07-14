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
start_date = requests.GET.get("start_date")
end_date = requests.GET.get("end_date")
team = requests.GET.get("team_name")
if team:
    team = team.lower()
else:
    team = ""

response = requests.get("https://api.balldontlie.io/v1/games", headers = headers, params = params)

data = response.json()
print(f"Found {len(data['data'])} games for {today}:\n")

for game in data["data"]:
    break