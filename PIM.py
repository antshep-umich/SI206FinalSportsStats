import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.hockeydb.com"

def get_team_links(main_url):
    """Scrape team names and links from the main page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(main_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to load main page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    team_links = []

    for link in soup.find_all("a", href=True):
        if link["href"].startswith("/stte/"):  # Filter for team links
            full_url = BASE_URL + link["href"]
            team_links.append((link.text.strip(), full_url))
    
    return team_links

def get_season_link(team_url):
    """Get the 2023-2024 season link from a team page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(team_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to load team page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the link with text "2023-24"
    link = soup.find("a", string="2023-24")
    if link and "href" in link.attrs:
        return BASE_URL + link["href"]
    
    print(f"No 2023-2024 season link found for {team_url}")
    return None

def get_player_stats(season_url):
    """Scrape player statistics from the season page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(season_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to load season page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    stats_table = soup.find("table", {"class": "sortable autostripe st"})

    if not stats_table:
        print(f"No stats table found at {season_url}")
        return []

    players = []
    rows = stats_table.find_all("tr")[1:]  # Skip header row
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 10:  # Ensure there are enough columns
            continue
        player = {
            "Number": cells[0].text.strip(),
            "Player Name": cells[1].text.strip(),
            "Position": cells[2].text.strip(),
            "Games Played": cells[3].text.strip(),
            "Goals": cells[4].text.strip(),
            "Assists": cells[5].text.strip(),
            "Points": cells[6].text.strip(),
            "Penalty Minutes": cells[7].text.strip(),
            "Birthplace": cells[8].text.strip(),
            "Age": cells[9].text.strip()
        }
        players.append(player)
    
    return players

def main():
    main_url = "https://www.hockeydb.com/ihdb/stats/team_data.php?x=99&y=16&tname=&tcity=&tstate=&tleague=NCAA&y1=2023&y2=2024&college=on"
    team_links = get_team_links(main_url)
    print(f"Found {len(team_links)} teams.")
    
    all_player_stats = []
    
    for team_name, team_link in team_links[:5]:  # Limit to 5 teams for testing
        print(f"Processing team: {team_name}, Link: {team_link}")
        season_link = get_season_link(team_link)
        if not season_link:
            print(f"No 2023-2024 season link found for team: {team_name}")
            continue
        
        print(f"Processing season: {season_link}")
        player_stats = get_player_stats(season_link)
        all_player_stats.extend(player_stats)
        print(f"Scraped {len(player_stats)} players from {team_name}")

    # Output all player stats
    for player in all_player_stats:
        print(player)

if __name__ == "__main__":
    main()
