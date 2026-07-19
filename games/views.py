import requests
from django.shortcuts import render

def game_listing(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    team = request.GET.get("team_name", "").lower()

    wins = {}
    games = []
    submit = False
    error = None

    if start_date and end_date:
        submit = True

        current_date = start_date
        all_events = []

        try:
            url = f"https://cache.sportsblaze.com/boxscores/nba/{start_date}"
            response = requests.get(url, timeout=30)
            data = response.json()

            events = data.get('events', [])

            for event in events:
                teams = event.get('teams', {})
                home = teams.get('home', {})
                away = teams.get('away', {})
                scores = event.get('scores', {}).get('total', {})

                home_team = home.get('name', 'Unknown')
                away_team = away.get('name', 'Unknown')
                home_score = scores.get('home', 0)
                away_score = scores.get('away', 0)

                if team:
                    if team not in home_team.lower() and team not in away_team.lower():
                        continue

                if home_score > away_score:
                    winner = home_team
                    wins[home_team] = wins.get(home_team, 0) + 1
                elif home_score < away_score:
                    winner = away_team
                    wins[away_team] = wins.get(away_team, 0) + 1
                else:
                    winner = "Draw"

                games.append({
                    "date": event.get('date', start_date),
                    "home_team": home_team,
                    "visitor_team": away_team,
                    "visitor_score": away_score,
                    "home_score": home_score,
                    "winner": winner,
                })

        except requests.exceptions.Timeout:
            error = "The request to the SportsBlaze API timed out. Please try again."
            games = []
            wins = {}
        except requests.exceptions.RequestException as e:
            error = f"Failed to fetch data: {str(e)}"
            games = []
            wins = {}
        except Exception as e:
            error = f"An unexpected error occurred: {str(e)}"
            games = []
            wins = {}

    winning_stats = dict(sorted(wins.items(), key=lambda x: x[1], reverse=True))

    return render(request, "gameListing.html", {
        "games_list": games,
        "winning_stats": winning_stats,
        "submit": submit,
        "error": error,
    })