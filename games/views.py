from django.shortcuts import render
import requests
import os
import time

def game_listing(request):
    api_key = os.environ.get('BALLDONTLIE_API_KEY')
    headers = {"Authorization": api_key}

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    team = request.GET.get("team_name", "").lower()

    wins = {}
    games = []
    submit = False
    error = None
    limit = False

    if start_date and end_date:
        submit = True
        
        params = {
            "per_page": 100,
            "start_date": start_date,
            "end_date": end_date,
        }

        try:
            while True:
                response = requests.get("https://api.balldontlie.io/v1/games", headers=headers, params=params)
                
                if response.status_code == 429:
                    limit = True
                    time.sleep(10)
                    continue
                
                if response.status_code != 200:
                    error = f"API returned status {response.status_code}"
                    break

                    
                data = response.json()
                
                
                for game in data["data"]:
                    home_team = game["home_team"]["full_name"]
                    visitor_team = game["visitor_team"]["full_name"]
                    
                    if team:
                        if team not in home_team.lower() and team not in visitor_team.lower():
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
                    
                meta = data.get("meta", {})
                next_cursor = meta.get("next_cursor")
                
                if not next_cursor:
                    break
                    
                params["cursor"] = next_cursor
                
        except Exception as e:
            error = f"Error: {e}"

    winning_stats = dict(sorted(wins.items(), key=lambda x: x[1], reverse=True))

    return render(request, "gameListing.html", {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit,
        "error": error,
        "limit": limit,
    })