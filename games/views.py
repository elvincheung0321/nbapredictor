from django.shortcuts import render
import requests
from datetime import date

def game_listing(request):
    auth_token = "26af8e03-7266-4878-a6ce-6890a733f7d5"
    headers = {"Authorization": auth_token}
    #today = "2026-06-13"

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    team = request.GET.get("team_name")
    if team:
        team = team.lower()
    else:
        team = ""

    params = {
        "cursor": 0,
        "per_page": 100,
        "start_date": start_date,
        "end_date": end_date,
    }


    response = requests.get("https://api.balldontlie.io/v1/games", headers = headers, params = params)

    data = response.json()

    for game in data["data"]:
        if team:
            home_name = game[""]
auth_token = "26af8e03-7266-4878-a6ce-6890a733f7d5"
headers = {"Authorization": auth_token}
start_date = requests.GET.get("start_date")
end_date = requests.GET.get("end_date")
params = {
    "cursor": 0,
    "per_page": 100,
    "start_date": start_date,
    "end_date": end_date,
}
response = requests.get("https://api.balldontlie.io/v1/games", headers = headers, params = params)
data = response.json()
print(data["data"])