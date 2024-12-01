from bs4 import BeautifulSoup
import re
import requests

def getSalary(playerName):
    url = "https://capwages.com/players/" + playerName
    req = requests.get(url).text
    print(req)
    soup = BeautifulSoup(req, 'html.parser')

