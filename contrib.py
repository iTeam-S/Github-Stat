import sys
import requests
import mysql.connector
from bs4 import BeautifulSoup
from os import environ as env
from datetime import date

if len(sys.argv) > 1:
    annee = sys.argv[1]
else:
 annee = None

def extract_contrib(elements):
    for el in elements:
        if 'contributions' in el.text:
            return el.get_text().strip().split('contributions')[0].strip().replace(',','')
    return 0

db = mysql.connector.connect(
    host='iteam-s.mg',
    user=env.get('ITEAMS_DB_USER'),
    password=env.get('ITEAMS_DB_PASSWORD'),
    database='ITEAMS'
    )
cursor = db.cursor()
cursor.execute('''
   SELECT user_github FROM membre m LEFT JOIN fonction f ON m.id = f.id_membre
   LEFT JOIN poste p ON f.id_poste = p.id
   WHERE m.actif = TRUE AND p.categorie = 'Dev' 
''')

resultat = dict()

for user in cursor:
    res = requests.get(f'https://github.com/{user[0]}?tab=overview' + ('' if annee else f'&from={annee}-01-01&to={annee}-10-25'))
    soup = BeautifulSoup(res.text, 'html.parser')
    res = soup.find_all('h2', class_='f4')
    resultat[user[0]] = int(extract_contrib(res))

print('CONTRIBUTIONS GITHUB', annee)
resultat = dict(sorted(resultat.items(), key=lambda item: item[1], reverse=True))
for res in enumerate(resultat.items(), start=1):
    print(f'{res[0]} - {res[1][0]}: {res[1][1]}')
