import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re

# Function to get page content with headers
def get_page_content(url, proxies=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

# Function to get all team links from the main NCAA page
def get_team_links(base_url):
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
def set_up_ncaa_table(players, cur, conn):
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
    base_url = "https://www.hockeydb.com/ihdb/stats/team_data.php?x=99&y=16&tname=&tcity=&tstate=&tleague=NCAA&y1=2023&y2=2024&college=on"
    proxies = None  # Set proxy if needed

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
            set_up_ncaa_table(players_data, cur, conn)
            print(f"Data for {team_name} added to the database.")
        else:
            print(f"No player data found for {team_name}.")

# Connect to the SQLite database and run the scraper
if __name__ == "__main__":
    conn = sqlite3.connect("players2324.db")
    cur = conn.cursor()

    get_college_players(cur, conn)

    cur.close()
    conn.close()
