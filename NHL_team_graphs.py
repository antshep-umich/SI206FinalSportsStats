import unittest
import sqlite3
import json
import os
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import csv

def read_team_csv(filename):
    """
    Reads team-related player information from a CSV file.

    Parameters
    -----------------------
    filename: str
        The name of the CSV file to read data from.

    Returns
    -----------------------
    data: list of lists
        A list of lists, each representing a row of the CSV file.
    """
    data = []

    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        
        header = next(csvreader)
        data.append(header)
        
        for row in csvreader:
            data.append(row)
    
    print(data)
    return data

def goals_per_mil_graph(data):
    """
    Reads team-related player information from a CSV file.

    Parameters
    -----------------------
    data: list of lists
        A list of lists, each representing a row of the CSV file.

    Returns
    -----------------------
    None
    """
    teams = []
    goals_per_million = []

    for team in data[1:]:
        teams.append(team[0])
        goals_per_million.append(float(team[4]))

    print(list(zip(teams, goals_per_million)))

    sorted_data = sorted(zip(teams, goals_per_million), key=lambda x: x[1], reverse=True)
    sorted_teams, sorted_goals_per_million = zip(*sorted_data)

    plt.figure(figsize=(10, 6))
    plt.bar(sorted_teams, sorted_goals_per_million, color='skyblue')
    plt.xlabel('Team')
    plt.ylabel('Goals per Million $')
    plt.title('Goals per Million $ by NHL Team')
    plt.xticks(rotation=90)
    plt.ylim(0, max(sorted_goals_per_million) + 1)

    plt.tight_layout() 
    plt.show()

def penalties_per_mil_graph(data):
    """
    Reads team-related player information from a CSV file.

    Parameters
    -----------------------
    data: list of lists
        A list of lists, each representing a row of the CSV file.

    Returns
    -----------------------
    None
    """
    teams = []
    penalties_per_million = []

    for team in data[1:]:
        teams.append(team[0])
        penalties_per_million.append(float(team[5]))

    print(list(zip(teams, penalties_per_million)))

    sorted_data = sorted(zip(teams, penalties_per_million), key=lambda x: x[1], reverse=True)
    sorted_teams, sorted_penalties_per_million = zip(*sorted_data)

    plt.figure(figsize=(10, 6))
    plt.bar(sorted_teams, sorted_penalties_per_million, color='skyblue')
    plt.xlabel('Team')
    plt.ylabel('Penalties per Million $')
    plt.title('Penalties per Million $ by NHL Team')
    plt.xticks(rotation=90)
    plt.ylim(0, max(sorted_penalties_per_million) + 1)

    plt.tight_layout() 
    plt.show()


def penalties_vs_goals_per_mil_graph(data):
    teams = []
    penalties_per_million = []
    goals_per_million = []

    for team in data[1:]:
        teams.append(team[0])
        goals_per_million.append(float(team[4]))
        penalties_per_million.append(float(team[5]))

    plt.figure(figsize=(10, 6))
    plt.scatter(goals_per_million, penalties_per_million, color='skyblue')

    for i, team in enumerate(teams):
        plt.annotate(team, (goals_per_million[i], penalties_per_million[i]), fontsize=8, alpha=0.75)

    plt.xlabel('Goals per Million')
    plt.ylabel('Penalties per Million')
    plt.title('Penalties vs Goals per Million for each NHL Team')

    plt.tight_layout()

    z = np.polyfit(goals_per_million, penalties_per_million, 1)
    p = np.poly1d(z)
    
    plt.plot(goals_per_million, p(goals_per_million), 'r', label=f'Pens = {z[1]:.2f} + {z[0]:.2f} * Goals')
    plt.legend(fontsize=9)

    plt.show()

def team_graphs():
    filename = 'NHL_teams.csv'
    data = read_team_csv(filename)
    goals_per_mil_graph(data)
    penalties_per_mil_graph(data)
    penalties_vs_goals_per_mil_graph(data)
