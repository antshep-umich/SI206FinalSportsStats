import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Function to get page content with headers


def get_page_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

# Function to get all team links from the main NCAA page
def get_team_links(base_url):
    soup = get_page_content(base_url)
    team_links = []
    for td in soup.find_all('td', class_='tp'):  # Locate all <td> with class 'tp'
        link_tag = td.find('a')
        if link_tag and 'href' in link_tag.attrs:
            team_links.append("https://www.hockeydb.com" + link_tag['href'])
    return team_links

# Function to check if a team has an active 2023-2024 season and return the season link
def get_season_link(team_url):
    soup = get_page_content(team_url)
    
    # Locate the specific row containing the 2023-24 season
    for row in soup.find_all('tr'):
        season_link = row.find('a', href=True)
        if season_link and '2023-24' in season_link.text:
            return "https://www.hockeydb.com" + season_link['href']
    
    return None

# Function to scrape player data from the 2023-2024 season page
def scrape_players(season_url, team_name):
    soup = get_page_content(season_url)
    players_data = []
    table = soup.find('table')
    if table:
        for row in table.find_all('tr')[1:]:  # Skip the header row
            cells = row.find_all('td')
            if cells:
                player = {
                    'Team': team_name,
                    'Name': cells[0].get_text(strip=True),
                    'Position': cells[1].get_text(strip=True),
                    'GP': cells[2].get_text(strip=True),
                    'G': cells[3].get_text(strip=True),
                    'A': cells[4].get_text(strip=True),
                    'PTS': cells[5].get_text(strip=True),
                    'PIM': cells[6].get_text(strip=True)
                }
                players_data.append(player)
    return players_data

# Main function
def main():
    base_url = "https://www.hockeydb.com/ihdb/stats/team_data.php?x=99&y=16&tname=&tcity=&tstate=&tleague=NCAA&y1=2023&y2=2024&college=on"
    try:
        soup = get_page_content(base_url)
        print("Successfully fetched the page!")
        # Add your scraping logic here
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching page: {e}")

# Run the script
if __name__ == "__main__":
    main()
