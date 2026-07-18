from django.shortcuts import render
import requests
from datetime import date
from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd

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

        # params = {
        #     "cursor": 0,
        #     "per_page": 100,
        #     "start_date": start_date,
        #     "end_date": end_date,
        # }

        # while True:
        game = leaguegamefinder.LeagueGameFinder(date_from_nullable=start_date, date_to_nullable=end_date)

        # df = game.get_data_frames()[0]
        # df2 = df.sort_values("GAME_ID").reset_index()   
        
        df1 = game.get_data_frames()[0].sort_values("GAME_ID").reset_index().drop("index", axis=1)
        home_game = df1[df1["MATCHUP"].str.contains("@")].reset_index().drop("index", axis=1)
        away_game = df1[-df1["MATCHUP"].str.contains("@")].reset_index().drop("index", axis=1)
        data = pd.merge(home_game, away_game, on=["GAME_ID", "GAME_DATE", "SEASON_ID"], suffixes=["_H","_A"])

        # data = data.drop("index", axis=1)
        
        for i, game in data.iterrows():
            home_team = game["TEAM_NAME_H"]
            home_ab = game["TEAM_ABBREVIATION_A"]
            visitor_ab = game["TEAM_ABBREVIATION_H"]
            visitor_team = game["TEAM_NAME_A"]
            if team:
                home_name = home_team.lower()
                visitor_name = visitor_team.lower()
                if team not in home_name and team not in visitor_name and team not in home_ab and team not in visitor_ab:
                    continue

            home_score = game["PTS_H"]
            visitor_score = game["PTS_A"]

            if home_score > visitor_score:
                winner = home_team
                wins[home_team] = wins.get(home_team, 0) + 1
            elif home_score < visitor_score:
                winner = visitor_team
                wins[visitor_team] = wins.get(visitor_team, 0) + 1
            else:
                winner = "Draw"

            games.append({
                "date": game["GAME_DATE"],
                "home_team": home_team,
                "visitor_team": visitor_team,
                "visitor_score": visitor_score,
                "home_score": home_score,
                "winner": winner,
            })
            # next_cursor = data.get("meta", {}).get("next_cursor")
            # params["cursor"] = next_cursor
            # if not next_cursor:
            #     break

    winning_stats = dict(sorted(wins.items(), key = lambda x: x[1], reverse = True))

    return render(request, "gameListing.html", {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit
    })
