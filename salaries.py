from bs4 import BeautifulSoup
import re
import requests

def getSalary(playerName):
    #url = "https://capwages.com/players/" + playerName
    url = "https://www.hockeydb.com/ihdb/stats/leagues/seasons/teams/0070752024.html"
    req = requests.get(url).text
    print(req)
    soup = BeautifulSoup(req, 'html.parser')

