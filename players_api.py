#from bs4 import BeautifulSoup
import re
import sqlite3
import os
#import unittest
from nhlpy.api.query.builder import QueryBuilder, QueryContext
from nhlpy.nhl_client import NHLClient
from nhlpy.api.query.filters.draft import DraftQuery
from nhlpy.api.query.filters.season import SeasonQuery
from nhlpy.api.query.filters.game_type import GameTypeQuery
from nhlpy.api.query.filters.position import PositionQuery, PositionTypes


def get_player_data():
    client = NHLClient(verbose=True)
    filters = [
        GameTypeQuery(game_type="2"),
        SeasonQuery(season_start="20232024", season_end="20232024")
    ]
    query_builder = QueryBuilder()
    query_context: QueryContext = query_builder.build(filters=filters)
    data = client.stats.skater_stats_with_query_context(
        report_type='summary',
        query_context=query_context,
        aggregate=True
    )
    return data

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
    Sets up the Players table in the database using the provided Pokemon data.

    Parameters
    -----------------------
    data: list
        List of Player data in JSON format.

    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    None
    """
    cur.execute(
            "CREATE TABLE IF NOT EXISTS Players (player_id INTEGER PRIMARY KEY, name TEXT UNIQUE, salary INTEGER, games INTEGER, points INTEGER, penalty_min INTEGER, avg_icetime INTEGER, goals INTEGER, assists INTEGER, plus_minus INTEGER, shooting_perc FLOAT)"
        )
    for player in data['data']:
        cur.execute(
            "INSERT OR IGNORE INTO Players (name, salary, games, points, penalty_min, avg_icetime, goals, assists, plus_minus, shooting_perc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (player['skaterFullName'],None,player['gamesPlayed'],player['points'],player['penaltyMinutes'],player['timeOnIcePerGame'],player['goals'],player['assists'],player['plusMinus'],player['shootingPct'])
        )
    conn.commit()

def main():
    #set_up_player_table(get_player_data(), *set_up_database('players2324.db'))
    print(get_player_data())


main()