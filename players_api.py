#from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import PIM
#import unittest
from nhlpy.api.query.builder import QueryBuilder, QueryContext
from nhlpy.nhl_client import NHLClient
#from nhlpy.api.query.filters.draft import DraftQuery
from nhlpy.api.query.filters.season import SeasonQuery
from nhlpy.api.query.filters.game_type import GameTypeQuery
#from nhlpy.api.query.filters.position import PositionQuery, PositionTypes

def get_player_data():
    """
    Gets a dictionary containing all player stats from the 23/24 season from the NHL API.
    Goes through a wrapper from https://github.com/coreyjs/nhl-api-py

    Parameters
    -----------------------
    none

    Returns
    -----------------------
    Dictionary {'data':[{player_id, name, games, points, penalty_min, avg_icetime, goals, assists, plus_minus, shooting_perc}]}:
        A dictionary containing a list of players and their stats for the season.
    """
    client = NHLClient(verbose=True)
    filters = [
        GameTypeQuery(game_type="2"),
        SeasonQuery(season_start="20232024", season_end="20232024")
    ]
    query_builder = QueryBuilder()
    query_context: QueryContext = query_builder.build(filters=filters)
    start = 0
    limit = 100
    skater_stats = {"data": []}
    while True:
        response = client.stats.skater_stats_with_query_context(
            report_type="summary",
            query_context=query_context,
            aggregate=False,
            start=start,
            limit=limit,
        )
        if not response["data"]:
            break
        skater_stats["data"].extend(response["data"])
        start += limit
    return skater_stats

def set_up_database(db_name):
    """
    Sets up a SQLite database connection and cursor.

    Parameters
    -----------------------
    db_name: str
        The name of the SQLite database.

    Returns
    -----------------------
    Tuple (Cursor, Connection):
        A tuple containing the database cursor and connection objects.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    return cur, conn

def set_up_player_table(data, cur, conn):
    """
    Sets up the Players table in the database using the provided NHL Player data.
    Calls the add_salary function to get salary data and add it to the DB from the Puckpedia api.

    Parameters
    -----------------------
    data: dictionary
        dictionary of Player data in JSON format.

    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    None
    """
    team_dict = {}
    cur.execute(
            "CREATE TABLE IF NOT EXISTS Players (player_id INTEGER PRIMARY KEY, name TEXT, team_id INTEGER, salary INTEGER, games INTEGER, points INTEGER, penalty_min INTEGER, avg_icetime INTEGER, goals INTEGER, assists INTEGER, plus_minus INTEGER, shooting_perc FLOAT)"
    )
    cur.execute(
            "CREATE TABLE IF NOT EXISTS NHL_Teams (team_id INTEGER PRIMARY KEY, name TEXT)"
    )

    cur.execute(
            "SELECT player_id FROM Players"
    )
    playerLen = len(cur.fetchall())
    if playerLen < 100:
        data['data'] = data['data'][playerLen:playerLen+25]

    for player in data['data']:
        if player['teamAbbrevs'] not in team_dict.keys():
            team_dict[player['teamAbbrevs']] = len(team_dict)
        cur.execute(
            "INSERT OR IGNORE INTO Players (player_id, name, team_id, games, points, penalty_min, avg_icetime, goals, assists, plus_minus, shooting_perc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (player['playerId'],player['skaterFullName'], team_dict[player['teamAbbrevs']], player['gamesPlayed'],player['points'],player['penaltyMinutes'],player['timeOnIcePerGame'],player['goals'],player['assists'],player['plusMinus'],player['shootingPct'])
        )
    for name, id in team_dict.items():
        cur.execute(
                "INSERT OR IGNORE INTO NHL_Teams (team_id, name) VALUES (?, ?)", (id, name)
            )
    conn.commit()
    add_salary(cur,conn)

def add_salary(cur, conn):
    """
    Adds player salary data from Puckpedia API.

    Parameters
    -----------------------
    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    Nothing
    """
    with open("puckAPI.txt", "r") as file:
        apikey = file.read()  # Reads the entire file
    response = requests.get(apikey)
    if response.status_code == 200:
        # Parse the JSON response into a Python dict
        data = response.json()

        cur.execute(
            "SELECT player_id FROM Players"
        )
        players = cur.fetchall()
        players = [x[0] for x in players]

        for player in data["data"]:
            if player['nhl_id'] and int(player['nhl_id']) in players:
                try:
                    cur.execute(
                        "UPDATE Players SET salary = ? WHERE player_id = ?", 
                        (int(player['current'][0]['current_season_cap_hit']),
                         int(player['nhl_id']))
                    )
                except:
                    print("Failed to get contract data")
        conn.commit()
    else:
        print(f"Request failed with status code {response.status_code}")

def testpd():
    """Just a test function

    Parameters
    -----------------------
    Nothing

    Returns
    -----------------------
    Nothing
    """
    client = NHLClient(verbose=True)
    filters = [
        GameTypeQuery(game_type="2"),
        SeasonQuery(season_start="20232024", season_end="20232024")
    ]
    query_builder = QueryBuilder()
    query_context: QueryContext = query_builder.build(filters=filters)
    start = 0
    limit = 1
    skater_stats = {"data": []}
    response = client.stats.skater_stats_with_query_context(
        report_type="summary",
        query_context=query_context,
        aggregate=False,
        start=start,
        limit=limit,
    )
    skater_stats["data"].extend(response["data"])
    start += limit
    print(skater_stats["data"])
    return None

def get_data():
    """
    Calls the set_up_player_table function and the PIM.get_college_players function.

    Parameters
    -----------------------
    Nothing

    Returns
    -----------------------
    Nothing
    """
    set_up_player_table(get_player_data(), *set_up_database('players2324.db'))
    #print(get_player_data())
    PIM.get_college_players(*set_up_database('players2324.db'))
    #testpd()

#def main():
    #get_data()

#main()