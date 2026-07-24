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
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "nba_model.pkl")
CSV_PATH = os.path.join(BASE_DIR, "2025_26_games.csv")

logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"MODEL_PATH: {MODEL_PATH}")
logger.info(f"CSV_PATH: {CSV_PATH}")
logger.info(f"Model exists? {os.path.exists(MODEL_PATH)}")
logger.info(f"CSV exists? {os.path.exists(CSV_PATH)}")

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

_model = None
_df = None
_accuracy = None

def get_model():
    global _model
    if _model is None:
        try:
            if os.path.exists(MODEL_PATH):
                _model = joblib.load(MODEL_PATH)
                logger.info("Model loaded successfully")
            else:
                logger.error(f"Model file NOT FOUND at {MODEL_PATH}")
                _model = None
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            _model = None
    return _model

def get_dataframe():
    global _df
    if _df is None:
        try:
            if os.path.exists(CSV_PATH):
                _df = pd.read_csv(CSV_PATH)
                logger.info("CSV loaded successfully")
            else:
                logger.error(f"CSV file NOT FOUND at {CSV_PATH}")
                _df = None
        except Exception as e:
            logger.error(f"Error loading CSV: {e}", exc_info=True)
            _df = None
    return _df

def get_accuracy():
    global _accuracy
    if _accuracy is None:
        model = get_model()
        df = get_dataframe()
        if model is not None and df is not None:
            try:
                X = df[FEATURES]
                y = df["home_win"]
                _accuracy = round((model.score(X, y) * 100), 1)
                logger.info(f"Accuracy calculated: {_accuracy}%")
            except Exception as e:
                logger.error(f"Error calculating accuracy: {e}", exc_info=True)
                _accuracy = "N/A"
        else:
            _accuracy = "N/A"
    return _accuracy

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

    accuracy = get_accuracy()

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
                    response = requests.get(
                        "https://api.balldontlie.io/v1/games",
                        headers=headers,
                        params=params,
                        timeout=60
                    )

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

    context = {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit,
        "error": error,
        "start_date": start_date,
        "end_date": end_date,
        "team": team,
        "accuracy": accuracy,
        "model_available": get_model() is not None and get_dataframe() is not None,
    }
    return render(request, "gameListing.html", context)

def predict(request):
    try:
        game_idx = request.GET.get("game_idx")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        team = request.GET.get("team_name", "").lower()
        cache_key = f"nba_games_{start_date}_{end_date}_{team}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return JsonResponse({"error": "Game data not found in cache"}, status=404)

        games = cached_data.get("games", [])
        idx = int(game_idx)
        game = games[idx]

        df = get_dataframe()
        model = get_model()

        if df is None or model is None:
            return JsonResponse({"error": "Model or data not available"}, status=503)

        csv_row = None
        for i, row in df.iterrows():
            if row["date"] == game["date"] and row["home_name"] == game["home_team"] and row["visitor_name"] == game["visitor_team"]:
                csv_row = row
                break

        if csv_row is None:
            return JsonResponse({"error": "Game data not found in CSV"}, status=404)

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
        logger.error(f"Prediction error: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)