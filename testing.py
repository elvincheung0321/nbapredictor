# import requests
# import pandas as pd
# import time

# api_key = "92799143-1160-4401-8d10-24d2b387a2c2"
# headers = {"Authorization": api_key}
# start_date = "2025-10-20"
# end_date = "2026-06-13"


# games_list = []
# cursor = None

# while True:

#     params = {
#         "per_page": 100,
#         "start_date": start_date,
#         "end_date": end_date,
#     }
    
#     if cursor:
#         params["cursor"] = cursor
    
#     response = requests.get("https://api.balldontlie.io/v1/games", headers=headers, params=params)
    

#     if response.status_code == 429:
#         print("API limit hit. Wait 10 seconds...")
#         time.sleep(10)
#         continue
    
#     data = response.json()
#     games = data["data"]

#     if not games:
#         break
    
#     for game in games:
#         games_list.append(game)
#     print(f"Found {len(games)} games (total: {len(games_list)})")
    

#     cursor = data["meta"].get("next_cursor")
    

#     if not cursor:
#         break
    
        

# print(f"\nTotal games found: {len(games_list)}")

# if games_list:
#     df = pd.DataFrame(games_list)
#     print(f"Dataframe info: {df.shape}")
# else:
#     print("No games found")
#     df = pd.DataFrame() 



inputs = [
    "home_avg_points",
    "home_avg_points_allowed",
    "home_wins_percent",
    "away_avg_points", 
    "away_avg_points_allowed", 
    "away_wins_percent",
    "away_avg_difference", 
    "home_avg_difference", 
]
import pandas as pd
import requests
import time


def stats(start, end):
    api_key = "92799143-1160-4401-8d10-24d2b387a2c2"
    headers = {"Authorization": api_key}
    start_date = start
    end_date = end
    
    
    games_list = []
    cursor = None
    
    while True:
    
        params = {
            "per_page": 100,
            "start_date": start_date,
            "end_date": end_date,
        }
        
        if cursor:
            params["cursor"] = cursor
        
        response = requests.get("https://api.balldontlie.io/v1/games", headers=headers, params=params)
        
    
        if response.status_code == 429:
            print("API limit hit. Wait 20 seconds...")
            time.sleep(20)
            continue
        
        data = response.json()
        games = data["data"]
    
        if not games:
            break
        
        for game in games:
            games_list.append(game)
        print(f"Found {len(games)} games (total: {len(games_list)})")
        
    
        cursor = data["meta"].get("next_cursor")
        
    
        if not cursor:
            break
        
            
    
    print(f"\nTotal games found: {len(games_list)}")
    
    if games_list:
        df = pd.DataFrame(games_list)
        print(f"Dataframe info: {df.shape}")
        return df 
    else:
        print("No games found")
        df = pd.DataFrame()
        return df 
    
def clean_data(df):
    df1 = df
    df["home_win"] = (df["home_team_score"] > df["visitor_team_score"])
    df1["home_name"] = df["home_team"].apply(lambda x:x["full_name"])
    df1["visitor_name"] = df["visitor_team"].apply(lambda x:x["full_name"])
    
    df1["home_abbrev"] = df["home_team"].apply(lambda x:x['abbreviation'])
    df1["visitor_abbrev"] = df["visitor_team"].apply(lambda x:x['abbreviation'])
    df1 = df.drop(["period", "time", "status", "postponed", "datetime", "home_q1", "home_q2", "home_q3", "home_q4", "home_ot1", "home_ot2", "home_ot3", "home_timeouts_remaining", "home_in_bonus", "visitor_q1", "visitor_q2", "visitor_q3", "visitor_q4", "visitor_ot1", "visitor_ot2", "visitor_ot3", "visitor_timeouts_remaining", "visitor_in_bonus", "home_team", "visitor_team", "ist_stage", "id", "date", "season",], axis=1)
    
    df1["home_win"] = df["home_win"].astype(int)
    team_stats = {}
# team_choose = "SAS"

    for index, row in df1.iterrows():
        home = row["home_abbrev"]
        away = row["visitor_abbrev"]
    
        if home not in team_stats:
            team_stats[home] = {"points": [], "points_allowed": [], "wins": []}
        team_stats[home]["points"].append(row["home_team_score"])
        team_stats[home]["points_allowed"].append(row["visitor_team_score"])
        team_stats[home]["wins"].append(row["home_win"])
    
        if away not in team_stats:
            team_stats[away] = {"points": [], "points_allowed": [], "wins": []}
        team_stats[away]["points"].append(row["visitor_team_score"])
        team_stats[away]["points_allowed"].append(row["home_team_score"])
        team_stats[away]["wins"].append(1 - row["home_win"])
    
    # df_team = df1[(df1["visitor_abbrev"] == team_choose) | (df1["home_abbrev"] == team_choose)]
    
    team_game_count = {team: 0 for team in team_stats}
    
    home_avg_points = []
    home_avg_points_allowed = []
    home_avg_difference = []
    home_wins_percent = []
    away_avg_points = []
    away_avg_points_allowed = []
    away_avg_difference = []
    away_wins_percent = []


    for index, row in df1.iterrows(): 
        home = row["home_abbrev"]
        away = row["visitor_abbrev"]
        
        home_num = team_game_count[home]
        away_num = team_game_count[away]
        
    
        if home_num > 0:
            past_points = team_stats[home]["points"][:home_num]
            past_allowed_points = team_stats[home]["points_allowed"][:home_num]
            past_wins = team_stats[home]["wins"][:home_num]
            avg_points = sum(past_points) / home_num
            avg_points_allowed = sum(past_allowed_points) / home_num
            wins_percent = sum(past_wins) / home_num
            home_avg_points.append(avg_points)
            home_avg_points_allowed.append(avg_points_allowed)
            home_avg_difference.append(avg_points - avg_points_allowed)
            home_wins_percent.append(wins_percent)
        else:
            home_avg_points.append(team_stats[home]["points"][0])
            home_avg_points_allowed.append(team_stats[home]["points_allowed"][0])
            home_avg_difference.append(team_stats[home]["points"][0] - team_stats[home]["points_allowed"][0])
            home_wins_percent.append(team_stats[home]["wins"][0])
    
    
        if away_num > 0:
            past_points = team_stats[away]["points"][:away_num]
            past_allowed_points = team_stats[away]["points_allowed"][:away_num]
            past_wins = team_stats[away]["wins"][:away_num]
            avg_points = sum(past_points) / away_num
            avg_points_allowed = sum(past_allowed_points) / away_num
            wins_percent = sum(past_wins) / away_num
            away_avg_points.append(avg_points)
            away_avg_points_allowed.append(avg_points_allowed)
            away_avg_difference.append(avg_points - avg_points_allowed)
            away_wins_percent.append(wins_percent)
        else:
            away_avg_points.append(team_stats[away]["points"][0])
            away_avg_points_allowed.append(team_stats[away]["points_allowed"][0])
            away_avg_difference.append(team_stats[away]["points"][0] - team_stats[away]["points_allowed"][0])
            away_wins_percent.append(team_stats[away]["wins"][0])
    
        team_game_count[home] += 1
        team_game_count[away] += 1


    df1["home_avg_points"] = home_avg_points
    df1["home_avg_points_allowed"] = home_avg_points_allowed
    df1["home_avg_difference"] = home_avg_difference
    df1["home_wins_percent"] = home_wins_percent
    df1["away_avg_points"] = away_avg_points
    df1["away_avg_points_allowed"] = away_avg_points_allowed
    df1["away_avg_difference"] = away_avg_difference
    df1["away_wins_percent"] = away_wins_percent

    # print(df1[["home_abbrev", "visitor_abbrev", "home_avg_points", "away_avg_points"]].head())
    return df1
        
    
df = stats("2025-10-21", "2026-06-13")
df1 = clean_data(df)
print(df1)

