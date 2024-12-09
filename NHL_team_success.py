import unittest
import sqlite3
import json
import os
import numpy as np
from scipy import stats
import seaborn as sns
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


#def write_goals_per_million_salary(table, min_gp, min_pts, min_pen, cur, conn):






def main():
    cur, conn = set_up_database('players2324.db')
    

main()