import unittest
import sqlite3
import json
import os
import numpy as np
from scipy import stats

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


def get_player_points_pens(min_gp, min_pts, min_pen, cur, conn):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    min_gp: int
        Minimum number of games played.

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
    """

    query = '''
    SELECT name, points, penalty_min, games 
    FROM Players
    WHERE games >= ?  and points >= ? or penalty_min >= ?
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

def graph_points_pens(points, pens, names):
    """
    Creates a list with all player points for players with at least a minimum number of games played

    Parameters
    -----------------------
    points: list
        list of points by each player

    pens: list
        list of penalty minutes by each player

    names: list
        list of player names

    Returns
    -----------------------
    Nothing
    
    """
    plt.scatter(pens, points)
    plt.xlabel('Penalty Minutes')
    plt.ylabel('Points')
    plt.title('2023-24 NHL Players Points vs. Penalty Minutes')
    for i, txt in enumerate(names):
        if pens[i] >= 130 or points[i] >= 105:
            plt.annotate(txt, (pens[i], points[i]))
    
    z = np.polyfit(pens, points, 1).round(2)
    p = np.poly1d(z)
    plt.plot(pens, p(pens), 'r', label=f'Points = {z[1]} + {z[0]} * Penalty Minutes'.format(z[1],z[0]))
    plt.legend(fontsize=9)

    plt.show()





def main():
    cur, conn = set_up_database('players2324.db')
    points, penalty_min, names = get_player_points_pens(41, 30, 40,  cur, conn)
    graph_points_pens(points, penalty_min, names)

main()

