import unittest
import sqlite3
import json
import os
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import csv


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

def get_info(cur, conn):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    None

    Returns
    -----------------------
    Result: List of tuples
        A list of tuples representing players team, goals, penalty minutes, and salary
    """

    query = f'''
    SELECT NHL_Teams.name, goals, penalty_min, salary 
    FROM Players
    JOIN NHL_Teams
    ON Players.team_id = NHL_Teams.team_id
    '''
    
    cur.execute(query)
    result = cur.fetchall()
    
    return result


def write_team_csv(data, filename):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    data: List of tuples
        Each tuple contains player details including team name, goals, penalty minutes, and salary.

    filename: str
        The name of the CSV file to write data to.



    Returns
    -----------------------
    None

    """
    header = ['Team', 'Goals', 'Penalties', 'Salary', 'Goals/million', 'Penalties/million']

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)

        csvwriter.writerow(header)


        team_dict = {}
        processed_data = []

        for row in data:
            if row[3]:
                teams = row[0].split(',')
                goals = row[1]
                penalties = row[2]
                salary = row[3]

                for team in teams:
                    if team not in team_dict:
                        team_dict[team] = {'Goals': 0, 'Penalties': 0, 'Salary': 0}
                
                    team_dict[team]['Goals'] += goals
                    team_dict[team]['Penalties'] += penalties
                    team_dict[team]['Salary'] += salary
            
        for team, stats in team_dict.items():
            if stats['Salary'] > 0:
                team_dict[team]['goals_per_million'] = stats['Goals'] / (stats['Salary'] / 1000000)
                team_dict[team]['penalty_minutes_per_million'] = stats['Penalties'] / (stats['Salary'] / 1000000)
            else:
                team_dict[team]['goals_per_million'] = 0
                team_dict[team]['penalty_minutes_per_million'] = 0
            
            
        
        for team in team_dict:    
            row = [team, team_dict[team]['Goals'], team_dict[team]['Penalties'], team_dict[team]['Salary'],
                    round(team_dict[team]['goals_per_million'], 2), round(team_dict[team]['penalty_minutes_per_million'], 2)]
            csvwriter.writerow(row)


def main():
    cur, conn = set_up_database('players2324.db')
    data = get_info(cur, conn)
    write_team_csv(data, 'NHL_teams.csv')
    conn.close()

main()