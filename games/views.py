from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
import requests
import os
import time
import pandas as pd
import joblib
import numpy as np
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "model", "nba_model.pkl")
CSV_PATH = os.path.join(BASE_DIR, "2025_26_games.csv")

FEATURES = [
    "home_avg_points",
    "home_avg_points_allowed",
    "home_wins_percent",
    "away_avg_points",
    "away_avg_points_allowed",
    "away_wins_percent",
    "away_avg_difference",
    "home_avg_difference",
]

model = joblib.load(MODEL_PATH)
df = pd.read_csv(CSV_PATH)

X = df[FEATURES]
y = df["home_win"]
accuracy = round((model.score(X, y) * 100), 1)


def game_listing(request):
    api_key = os.environ.get("BALLDONTLIE_API_KEY")
    headers = {"Authorization": api_key}

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    team = request.GET.get("team_name", "").lower()

    wins = {}
    games = []
    submit = False
    error = None


    if start_date and end_date:
        submit = True

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_diff = (end - start).days

        if days_diff > 90:
            error = f"Date range is too large. Please select a range smaller than 90 days."
            return render(request, "gameListing.html", {
                "submit": submit,
                "error": error,
                "start_date": start_date,
                "end_date": end_date,
                "team": team,
                "accuracy": accuracy,
            })

        cache_key = f"nba_games_{start_date}_{end_date}_{team}"
        cached_data = cache.get(cache_key)

        if cached_data:
            games = cached_data.get("games", [])
            wins = cached_data.get("wins", {})
        else:
            params = {
                "per_page": 100,
                "start_date": start_date,
                "end_date": end_date,
            }

            try:
                while True:
                    response = requests.get("https://api.balldontlie.io/v1/games", headers=headers, params=params, timeout=60)

                    if response.status_code == 429:
                        time.sleep(10)
                        continue

                    if response.status_code != 200:
                        error = f"Status code: {response.status_code}"
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

                        can_predict = start_date >= "2025-10-20" and end_date <= "2026-06-13"

                        game_data = {
                            "date": game["date"],
                            "home_team": home_team,
                            "visitor_team": visitor_team,
                            "visitor_score": visitor_score,
                            "home_score": home_score,
                            "winner": winner,
                            "home_win": 1 if home_score > visitor_score else 0,
                            "predicted_winner": None,
                            "can_predict": can_predict,
                        }

                        games.append(game_data)

                    meta = data.get("meta", {})
                    next_cursor = meta.get("next_cursor")

                    if not next_cursor:
                        break
                    params["cursor"] = next_cursor


            except Exception as e:
                error = f"Error: {e}"

            if games:
                cache_data = {
                    "games": games,
                    "wins": wins,
                }
                cache.set(cache_key, cache_data, 3600)

        if games:
            session_key = f"predictions_{start_date}_{end_date}_{team}"
            predictions_dict = request.session.get(session_key, {})
            for idx, predicted_winner in predictions_dict.items():
                idx = int(idx)
                if idx < len(games):
                    games[idx]["predicted_winner"] = predicted_winner

    winning_stats = dict(sorted(wins.items(), key=lambda x: x[1], reverse=True))

    return render(request, "gameListing.html", {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit,
        "error": error,
        "start_date": start_date,
        "end_date": end_date,
        "team": team,
        "accuracy": accuracy,
    })


def predict(request):
    try:
        game_idx = request.GET.get("game_idx")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        team = request.GET.get("team_name", "").lower()
        cache_key = f"nba_games_{start_date}_{end_date}_{team}"
        cached_data = cache.get(cache_key)

        games = cached_data.get("games", [])

        idx = int(game_idx)
        game = games[idx]
        csv_row = None

        for i, row in df.iterrows():
            if row["date"] == game["date"] and row["home_name"] == game["home_team"] and row["visitor_name"] == game["visitor_team"]:
                csv_row = row
                break

        features = np.array([[
            csv_row["home_avg_points"],
            csv_row["home_avg_points_allowed"],
            csv_row["home_wins_percent"],
            csv_row["away_avg_points"],
            csv_row["away_avg_points_allowed"],
            csv_row["away_wins_percent"],
            csv_row["away_avg_difference"],
            csv_row["home_avg_difference"],
        ]])

        prediction = model.predict(features)[0]
        predicted_winner = game["home_team"] if prediction == 1 else game["visitor_team"]

        session_key = f"predictions_{start_date}_{end_date}_{team}"
        predictions_dict = request.session.get(session_key, {})
        predictions_dict[str(idx)] = predicted_winner
        request.session[session_key] = predictions_dict

        return JsonResponse({
            "success": True,
            "predicted_winner": predicted_winner,
            "game_idx": idx,
        })

    except Exception as e:
        return JsonResponse({"error": e})