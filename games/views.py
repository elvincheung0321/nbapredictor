from django.shortcuts import render
import requests
from datetime import date

def game_listing(request):
    auth_token = "26af8e03-7266-4878-a6ce-6890a733f7d5"
    headers = {"Authorization": auth_token}

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    team = request.GET.get("team_name")
    if team:
        team = team.lower()
    else:
        team = ""

    wins = {}
    games = []
    submit = False

    if start_date and end_date:
        submit = True

        params = {
            "cursor": 0,
            "per_page": 100,
            "start_date": start_date,
            "end_date": end_date,
        }

        while True:
            response = requests.get("https://api.balldontlie.io/v1/games", headers=headers, params=params)
            if response.status_code != 200:
                break
            
            data = response.json()
            
            for game in data["data"]:
                home_team = game["home_team"]["full_name"]
                visitor_team = game["visitor_team"]["full_name"]
                if team:
                    home_name = home_team.lower()
                    visitor_name = visitor_team.lower()
                    if team not in home_name and team not in visitor_name:
                        continue

                home_score = game["home_team_score"]
                visitor_score = game["visitor_team_score"]

                if home_score > visitor_score:
                    winner = home_team
                    wins[home_team] = wins.get(home_team, 0) + 1
                elif home_score < visitor_score:
                    winner = visitor_team
                    wins[visitor_team] = wins.get(visitor_team, 0) + 1
                else:
                    winner = "Draw"

                games.append({
                    "date": game["date"],
                    "home_team": home_team,
                    "visitor_team": visitor_team,
                    "visitor_score": visitor_score,
                    "home_score": home_score,
                    "winner": winner,
                })
            next_cursor = data.get("meta", {}).get("next_cursor")
            params["cursor"] = next_cursor
            if not next_cursor:
                break

    winning_stats = dict(sorted(wins.items(), key = lambda x: x[1], reverse = True))

    return render(request, "gameListing.html", {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit
    })
