import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import sqlite3
import csv

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
                    'Number': cells[0].get_text(strip=True),
                    'Name': cells[1].get_text(strip=True),
                    'Position': cells[2].get_text(strip=True),
                    'GP': cells[3].get_text(strip=True),
                    'G': cells[4].get_text(strip=True),
                    'A': cells[5].get_text(strip=True),
                    'PTS': cells[6].get_text(strip=True),
                    'PIM': cells[7].get_text(strip=True)
                }
                players_data.append(player)
    return players_data

# Check if team data exists in the CSV
def team_already_scraped(team_name, csv_file="scraped_teams.csv"):
    if os.path.exists(csv_file):
        scraped_teams = pd.read_csv(csv_file)
        return team_name in scraped_teams['Team'].values
    return False

# Add team to the CSV
def save_scraped_team(team_name, csv_file="scraped_teams.csv"):
    if not os.path.exists(csv_file):
        pd.DataFrame(columns=['Team']).to_csv(csv_file, index=False)
    scraped_teams = pd.read_csv(csv_file)
    scraped_teams = pd.concat([scraped_teams, pd.DataFrame({'Team': [team_name]})], ignore_index=True).drop_duplicates()
    scraped_teams.to_csv(csv_file, index=False)

def get_college_players(cur, conn):
    base_url = "https://www.hockeydb.com/ihdb/stats/team_data.php?x=99&y=16&tname=&tcity=&tstate=&tleague=NCAA&y1=2023&y2=2024&college=on"
    proxies = None  # Set proxy if needed

    try:
        team_links = get_team_links(base_url)
        all_players_data = []

        for team_url in team_links:
            team_name = team_url.split("/")[-1].replace("-", " ").title()
            print(f"Checking team: {team_name}...")

            if team_already_scraped(team_name):
                print(f"Skipping {team_name} (already scraped).")
                continue

            season_url = get_season_link(team_url)
            if not season_url:
                print(f"No active season found for {team_name}.")
                continue

            print(f"Active season found for {team_name}. Scraping player data...")
            players_data = scrape_players(season_url, team_name)
            all_players_data.extend(players_data)

            save_scraped_team(team_name)

            # Add delay to avoid being blocked
            time.sleep(8)

        # Save all players data to a CSV
        if all_players_data:
            players_df = pd.DataFrame(all_players_data)
            players_df.to_csv("players_data.csv", index=False)
            print("Player data saved to players_data.csv.")
            #Team,Number,Name,Position,GP,G,A,PTS,PIM
            cur.execute(
                "CREATE TABLE IF NOT EXISTS NCAAPlayers (player_id INTEGER PRIMARY KEY, name TEXT UNIQUE, games INTEGER, points INTEGER, penalty_min INTEGER, goals INTEGER, assists INTEGER)"
            )
            for player in players_df.iterrows():
                cur.execute(
                    "INSERT OR IGNORE INTO NCAAPlayers (name, games, points, penalty_min, goals, assists) VALUES (?, ?, ?, ?, ?, ?)", 
                    (player['Name'],player['GP'],player['PTS'],player['PIM'],player['G'],player['A'])
                )
            conn.commit()
        else:
            print("Reading player data from CSV.")
            players_df = pd.read_csv('players_data.csv')
            cur.execute(
                "CREATE TABLE IF NOT EXISTS NCAAPlayers (player_id INTEGER PRIMARY KEY, name TEXT UNIQUE, games INTEGER, points INTEGER, penalty_min INTEGER, goals INTEGER, assists INTEGER)"
            )
            for index, player in players_df.iterrows():
                cur.execute(
                    "INSERT OR IGNORE INTO NCAAPlayers (name, games, points, penalty_min, goals, assists) VALUES (?, ?, ?, ?, ?, ?)", 
                    (player['Name'],player['GP'],player['PTS'],player['PIM'],player['G'],player['A'])
                )
            conn.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
    
    return None

def set_up_ncaa_table(data, cur, conn):
    """
    Sets up the NCAA_Players and NCAA_Teams tables in the database using provided NCAA player data.

    Parameters
    -----------------------
    data: list
        List of NCAA player data in JSON or CSV format.

    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    None
    """
    team_dict = {}
    
    # Create tables if they don't exist
    cur.execute(
        "CREATE TABLE IF NOT EXISTS NCAA_Players (player_id INTEGER PRIMARY KEY, name TEXT UNIQUE, team_id INTEGER, games INTEGER, points INTEGER, penalty_min INTEGER, avg_icetime INTEGER, goals INTEGER, assists INTEGER, plus_minus INTEGER, shooting_perc FLOAT)"
    )
    
    cur.execute(
        "CREATE TABLE IF NOT EXISTS NCAA_Teams (team_id INTEGER PRIMARY KEY, name TEXT)"
    )
    
    # Loop through players and assign team_id
    for player in data:
        # Ensure that each team gets a unique team_id
        if player['teamName'] not in team_dict:
            team_dict[player['teamName']] = len(team_dict) + 1  # Ensuring unique IDs
        
        # Insert player data with corresponding team_id
        cur.execute(
            "INSERT OR IGNORE INTO NCAA_Players (player_id, name, team_id, games, points, penalty_min, avg_icetime, goals, assists, plus_minus, shooting_perc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (player['playerId'], player['playerName'], team_dict[player['teamName']],
             player['gamesPlayed'], player['points'], player['penaltyMinutes'],
             player['timeOnIcePerGame'], player['goals'], player['assists'],
             player['plusMinus'], player['shootingPct'])
        )
    
    # Insert teams into the NCAA_Teams table
    for name, team_id in team_dict.items():
        cur.execute(
            "INSERT OR IGNORE INTO NCAA_Teams (team_id, name) VALUES (?, ?)",
            (team_id, name)
        )
    
    conn.commit()

def parse_ncaa_data_from_csv(file_path):
    """
    Parses NCAA player data from a CSV file.

    Parameters
    -----------------------
    file_path: str
        Path to the CSV file.

    Returns
    -----------------------
    List of dictionaries:
        Parsed NCAA player data.
    """
    players = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            players.append({
                'playerId': int(row['player_id']),
                'playerName': row['name'],
                'teamName': row['team_name'],
                'gamesPlayed': int(row['games']),
                'points': int(row['points']),
                'penaltyMinutes': int(row['penalty_min']),
                'timeOnIcePerGame': float(row['avg_icetime']),
                'goals': int(row['goals']),
                'assists': int(row['assists']),
                'plusMinus': int(row['plus_minus']),
                'shootingPct': float(row['shooting_perc']),
            })
    return players