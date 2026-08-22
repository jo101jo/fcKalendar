import datetime
from datetime import timedelta
from icalendar import Calendar, Event
import requests

TEAM_NAME = "1. FC Köln"
LEAGUE_SHORTCUT = "bl1"  # Wenn der FC in der 2. Liga spielt, hier 'bl2' eintragen
SAISON = datetime.datetime.now().year


def get_fc_matches():
    url = f"https://api.openligadb.de/getmatchdata/{LEAGUE_SHORTCUT}/{SAISON}"
    response = requests.get(url)
    response.raise_for_status()
    matches = response.json()

    fc_matches = []
    for match in matches:
        team1 = match.get("team1", {}).get("teamName", "")
        team2 = match.get("team2", {}).get("teamName", "")

        if TEAM_NAME.lower() in team1.lower() or TEAM_NAME.lower() in team2.lower():
            fc_matches.append(match)

    return fc_matches


def create_ics(matches, output_filename="fc_koeln_spielplan.ics"):
    cal = Calendar()
    cal.add("prodid", "-//1. FC Köln Spielplan Generator//NONSGML v1.0//DE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "1. FC Köln Spielplan")
    cal.add("x-wr-timezone", "Europe/Berlin")

    for match in matches:
        event = Event()

        team1 = match["team1"]["teamName"]
        team2 = match["team2"]["teamName"]
        group_name = match.get("group", {}).get("groupName", "Spieltag")

        event.add("summary", f"{team1} vs. {team2}")

        match_date_str = match.get("matchDateTimeUTC") or match.get("matchDateTime")
        if not match_date_str:
            continue

        start_time = datetime.datetime.fromisoformat(
            match_date_str.replace("Z", "+00:00")
        )
        end_time = start_time + timedelta(hours=2)

        event.add("dtstart", start_time)
        event.add("dtend", end_time)

        # Sichere Abfrage für den Ort
        location_data = match.get("location") or {}
        city = location_data.get("locationCity", "")
        stadium = location_data.get("locationStadium", "")
        location_str = f"{stadium}, {city}".strip(", ")
        
        if location_str:
            event.add("location", location_str)

        description = f"{group_name} - {LEAGUE_SHORTCUT.upper()}\n"
        if match.get("matchIsFinished"):
            results = match.get("matchResults") or []
            if results:
                result1 = results[-1].get("pointsTeam1", 0)
                result2 = results[-1].get("pointsTeam2", 0)
                description += f"Endergebnis: {result1}:{result2}\n"

        event.add("description", description)
        event.add("uid", f"openligadb-match-{match['matchID']}@fckoeln")

        cal.add_component(event)

    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())

    print(f"Kalenderdatei '{output_filename}' wurde erfolgreich erstellt.")


if __name__ == "__main__":
    matches = get_fc_matches()
    create_ics(matches)