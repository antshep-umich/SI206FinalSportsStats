import unittest
import sqlite3
import json
import os
import numpy as np
from scipy import stats
import seaborn as sns
import NHL_team_graphs
import NHL_team_success

import matplotlib.pyplot as plt


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


def get_player_points_pens(table, min_gp, min_pts, min_pen, cur, conn):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    table: str
        Name of the table in the database.

    min_gp: int
        Minimum number of games played.
    
    min_pts: int
        Minimum number of points scored.

    min_pen: int
        Minimum number of penalty minutes.

    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    Points (list):
        A list containing entries for each player's point total.
    
    Penalty_min (list):
        A list containing entries for each player's penalty minute total.

    Names (list):
        A list containing entries for each player's name.
    """

    query = f'''
    SELECT name, points, penalty_min, games 
    FROM {table}
    WHERE games >= ? AND (points >= ? OR penalty_min >= ?)
    '''
    
    cur.execute(query, (min_gp, min_pts, min_pen))
    result = cur.fetchall()
    
    Points = []
    Penalty_min = []
    Names = []
    for player in result:
        Points.append(player[1])
        Penalty_min.append(player[2])
        Names.append(player[0])
    

    return Points, Penalty_min, Names

def get_pts_per_penalty_minute(table, min_gp, min_pts, min_pen, cur, conn):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    table: str
        Name of the table in the database.

    min_gp: int
        Minimum number of games played.
    
    min_pts: int
        Minimum number of points scored.

    min_pen: int
        Minimum number of penalty minutes.

    cur: Cursor
        The database cursor object.

    conn: Connection
        The database connection object.

    Returns
    -----------------------
    pts_per_pen: List
        list of values for points per penalty minute
    """

    query = f'''
    SELECT points, penalty_min
    FROM {table}
    WHERE games >= ? AND (points >= ? AND penalty_min >= ?)
    '''
    
    cur.execute(query, (min_gp, min_pts, min_pen))
    result = cur.fetchall()
    
    Points_per_pen = []
    for player in result:
        print(player)
        Points_per_pen.append(player[0]/player[1])
    

    return Points_per_pen

def graph_points_pens(points, pens, names, min_pts, min_pens, league):
    """
    Creates graphs of points against penalty minutes for NHL and NCAA players

    Parameters
    -----------------------
    points: list
        list of points by each player

    pens: list
        list of penalty minutes by each player

    names: list
        list of player names
    
    min_pts: int
        minimum number of points to display names
    
    min_pens: int
        minimum number of penalty minutes to display names

    Returns
    -----------------------
    Nothing
    
    """
    plt.scatter(pens, points)
    plt.xlabel('Penalty Minutes')
    plt.ylabel('Points')
    plt.title(f'2023-24 {league} Players Points vs. Penalty Minutes')
    for i, txt in enumerate(names):
        if pens[i] >= min_pens or points[i] >= min_pts:
            plt.annotate(txt, (pens[i], points[i]))
    
    z = np.polyfit(pens, points, 1).round(2)
    p = np.poly1d(z)
    plt.plot(pens, p(pens), 'r', label=f'Points = {z[1]} + {z[0]} * Penalty Minutes'.format(z[1],z[0]))
    plt.legend(fontsize=9)

    plt.show()

def graph_points_per_pen(Points_per_pen, league):
    """
    Creates graphs of points per penalty minute for the NHL and NCAA players

    Parameters
    -----------------------
    league: string
        NHL or NCAA

    pts_per_pen: List
        list of values for points per penalty minute

    Returns
    -----------------------
    Nothing
    
    """
    plt.figure(figsize=(10, 6))
        
    sns.histplot(Points_per_pen, bins=50, kde=True, color='blue')
        
    plt.xlabel('Points per penalty minute', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.title(f'2023-24 {league} Players Points per Penalty Minute', fontsize=16)

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xlim(left=0)
        
    plt.show()



def main():
    cur, conn = set_up_database('players2324.db')
    tables = {"Players": [41, 30, 40, 105, 130, "NHL"], "NCAA_Players": [16, 12, 15, 55, 70, "NCAA"]}
    for table, values in tables.items():
        points, penalty_min, names = get_player_points_pens(table, values[0], values[1], values[2], cur, conn)
        graph_points_pens(points, penalty_min, names, values[3], values[4], values[5])

    tables2 = {"Players": [10, 5, 5, "NHL"], "NCAA_Players": [5, 2, 2, "NCAA"]}
    for table, values in tables2.items():
        pts_per_pen = get_pts_per_penalty_minute(table, values[0], values[1], values[2], cur, conn)
        graph_points_per_pen(pts_per_pen, values[3])
    
    NHL_team_graphs.team_graphs()
    #NHL_team_success.write_csv()

    

main()

