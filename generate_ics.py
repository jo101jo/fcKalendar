import datetime
from datetime import timedelta
from icalendar import Calendar, Event
import requests

# Team und Saison definieren
TEAM_NAME = "1. FC Köln"
LEAGUE_SHORTCUT = "bl1"  # 'bl1' für 1. Bundesliga, 'bl2' für 2. Bundesliga
SAISON = datetime.datetime.now().year  # Startjahr der aktuellen/kommenden Saison


def get_fc_matches():
    # Alle Spiele der Saison von OpenLigaDB abrufen
    url = f"https://api.openligadb.de/getmatchdata/{LEAGUE_SHORTCUT}/{SAISON}"
    response = requests.get(url)
    response.raise_for_status()
    matches = response.json()

    fc_matches = []
    for match in matches:
        team1 = match.get("team1", {}).get("teamName", "")
        team2 = match.get("team2", {}).get("teamName", "")

        # Nur Spiele mit Beteiligung des 1. FC Köln filtern
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

        # Titel des Kalendereintrags
        event.add("summary", f"{team1} vs. {team2}")

        # Anstoßzeit verarbeiten (UTC/ISO-Format von OpenLigaDB)
        match_date_str = match.get("matchDateTimeUTC") or match.get("matchDateTime")
        if not match_date_str:
            continue

        start_time = datetime.datetime.fromisoformat(
            match_date_str.replace("Z", "+00:00")
        )
        # Spieldauer ca. 2 Stunden für den Kalender ansetzen
        end_time = start_time + timedelta(hours=2)

        event.add("dtstart", start_time)
        event.add("dtend", end_time)

        # Ort & Beschreibung festlegen
        location = match.get("location", {}).get("locationCity", "")
        if match.get("location", {}).get("locationStadium"):
            location = (
                f"{match['location']['locationStadium']}, {location}".strip(", ")
            )
        event.add("location", location)

        description = f"{group_name} - {LEAGUE_SHORTCUT.upper()}\n"
        if match.get("matchIsFinished"):
            result1 = match["matchResults"][-1]["pointsTeam1"]
            result2 = match["matchResults"][-1]["pointsTeam2"]
            description += f"Endergebnis: {result1}:{result2}\n"

        event.add("description", description)
        event.add("uid", f"openligadb-match-{match['matchID']}@fckoeln")

        cal.add_component(event)

    # ICS-Datei abspeichern
    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())

    print(f"Kalenderdatei '{output_filename}' wurde erfolgreich erstellt.")


if __name__ == "__main__":
    matches = get_fc_matches()
    create_ics(matches)