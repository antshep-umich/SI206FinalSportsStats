import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re

# Function to get page content with headers
def get_page_content(url):
    """
    Takes a URL and returns a BeautifulSoup object from the response.

    Parameters
    -----------------------
    URL:
        A website URL

    Returns
    -----------------------
    A BeautifulSoup object or nothing.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

# Function to get all team links from the main NCAA page
def get_team_links(base_url):
    """
    Gets all of the team URLs from the NCAA stats page with the teams listed.

    Parameters
    -----------------------
    base_url:
        The page URL for the NCAA team stats page.

    Returns
    -----------------------
    team_links:
        A list of URLs for the teams.
    """
    soup = get_page_content(base_url)
    if not soup:
        return []
    team_links = []
    for td in soup.find_all('td', class_='tp'):
        link_tag = td.find('a')
        if link_tag and 'href' in link_tag.attrs:
            team_links.append("https://www.hockeydb.com" + link_tag['href'])
    return team_links

# Function to check if a team has an active 2023-2024 season and return the season link
def get_season_link(team_url):
    """
    Checks a team's URL to see if they have a team listed for the 2023-2024 season
    and returns the link to that season's stats for the team.

    Parameters
    -----------------------
    team_url:
        A NCAA team's URL.

    Returns
    -----------------------
    Nothing or a string with the URL for the 2023-2024 season for that team.
    """
    soup = get_page_content(team_url)
    if not soup:
        return None
    for row in soup.find_all('tr'):
        season_link = row.find('a', href=True)
        if season_link and '2023-24' in season_link.text.lower():  # Case-insensitive
            return "https://www.hockeydb.com" + season_link['href']
    return None

# Function to scrape player data from the 2023-2024 season page
def scrape_players(season_url, team_name):
    """
    Scrapes the player data from the 2023-2024 season stats for a team.

    Parameters
    -----------------------
    season_url:
        The URL from get_season_link for this team.

    team_name:
        The team this data is for

    Returns
    -----------------------
    players_data:
        A list of player dictionaries with each player's stats.
    """
    soup = get_page_content(season_url)
    if not soup:
        return []
    players_data = []
    table = soup.find('table')
    if table:
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if cells and len(cells) >= 8:  # Ensure sufficient columns
                player = {
                    'Team': team_name,
                    'Name': cells[1].get_text(strip=True),
                    'Position': cells[2].get_text(strip=True),
                    'GP': int(cells[3].get_text(strip=True) or 0),
                    'G': int(cells[4].get_text(strip=True) or 0),
                    'A': int(cells[5].get_text(strip=True) or 0),
                    'PTS': int(cells[6].get_text(strip=True) or 0),
                    'PIM': int(cells[7].get_text(strip=True) or 0)
                }
                players_data.append(player)
    return players_data

# Function to handle database interactions
def set_up_ncaa_table(cur, conn):
    """
    Creates the NCAA_Teams and NCAA_Players tables in the DB if they don't exist.

    Parameters
    -----------------------
    cur:
        The database cursor

    conn:
        The database connection

    Returns
    -----------------------
    Nothing
    """
    # Create tables if not exist
    cur.execute("CREATE TABLE IF NOT EXISTS NCAA_Teams (team_id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS NCAA_Players (
            player_id INTEGER PRIMARY KEY,
            name TEXT,
            team_id INTEGER,
            games INTEGER,
            points INTEGER,
            penalty_min INTEGER,
            goals INTEGER,
            assists INTEGER,
            FOREIGN KEY(team_id) REFERENCES NCAA_Teams(team_id)
        )
    """)
    conn.commit()

def insert_player_data(players, cur, conn):
    """
    Iterates through the player data and adds any new data to the NCAA_Players table.

    Parameters
    -----------------------
    players:
        The list of player dictionaries from scrape_players
    
    cur:
        The database cursor
    
    conn:
        The database connection

    Returns
    -----------------------
    Nothing
    """
    # Track team IDs
    team_ids = {}

    # Insert team data and players
    for player in players:
        team_name = player['Team']
        # Check if team exists; if not, insert it
        if team_name not in team_ids:
            cur.execute("INSERT OR IGNORE INTO NCAA_Teams (name) VALUES (?)", (team_name,))
            cur.execute("SELECT team_id FROM NCAA_Teams WHERE name = ?", (team_name,))
            team_ids[team_name] = cur.fetchone()[0]

        # Insert player data
        cur.execute("""
            INSERT OR IGNORE INTO NCAA_Players (name, team_id, games, points, penalty_min, goals, assists)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player['Name'],
            team_ids[team_name],
            player['GP'],
            player['PTS'],
            player['PIM'],
            player['G'],
            player['A']
        ))

    conn.commit()

# Main function to scrape and save data to the database
def get_college_players(cur, conn):
    """
    Utilizes the prior defined functions in PIM.py to scrape and add player data.

    Parameters
    -----------------------
    cur:
        database cursor
    
    conn:
        database connection

    Returns
    -----------------------
    Nothing
    """
    base_url = "https://www.hockeydb.com/ihdb/stats/team_data.php?x=99&y=16&tname=&tcity=&tstate=&tleague=NCAA&y1=2023&y2=2024&college=on"
    proxies = None  # Set proxy if needed
    set_up_ncaa_table(cur, conn)

    team_links = get_team_links(base_url)

    for team_url in team_links:
        team_name = team_url.split("/")[-1].replace("-", " ").title()
        print(f"Checking team: {team_name}...")

        # Check if the team is already in the database
        cur.execute("SELECT team_id FROM NCAA_Teams WHERE name = ?", (team_name,))
        if cur.fetchone():
            print(f"Skipping {team_name} (already in database).")
            continue

        season_url = get_season_link(team_url)
        if not season_url:
            print(f"No active season found for {team_name}.")
            continue

        print(f"Active season found for {team_name}. Scraping player data...")
        players_data = scrape_players(season_url, team_name)

        # Save data to the database
        if players_data:
            insert_player_data(players_data, cur, conn)
            print(f"Data for {team_name} added to the database.")
        else:
            print(f"No player data found for {team_name}.")

# Connect to the SQLite database and run the scraper
"""if __name__ == "__main__":
    conn = sqlite3.connect("players2324.db")
    cur = conn.cursor()

    get_college_players(cur, conn)

    cur.close()
    conn.close()"""
