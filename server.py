import mysql.connector
import requests as req
from fastapi import FastAPI
from threading import Thread
from os import environ as env
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
webserver = FastAPI()


def point_git(repos_id):
    db = mysql.connector.connect(
        host='iteam-s.mg',
        user=env.get('ITEAMS_DB_USER'),
        password=env.get('ITEAMS_DB_PASSWORD')
    )
    cursor = db.cursor()

    cursor.execute("""
        SELECT repos FROM STAT_MEMBRE.projet WHERE id = %s
    """, (repos_id,))
    repos = cursor.fetchone()
    rep = repos[0].split('/')[-1]
    if rep.endswith('.git'):
        rep = rep.replace('.git', '')
    res = get_stat(rep, commit_only=True)
    for user in res['Users'].keys():
        cursor.execute("""
            UPDATE STAT_MEMBRE.membre_projet mp JOIN ITEAMS.membre m
            ON m.id = mp.id_membre SET point_git = %s
            WHERE m.user_github = %s AND mp.id_projet = %s
        """, (res['Users'][user]['commits'], user, repos_id))
        db.commit()
        #total expérience membre
        cursor.execute(
            """
                UPDATE ITEAMS.membre m 
                SET point_experience = IFNULL(m.point_experience, 0)  + 
                (SELECT (impact*25) + (implication*20) + (difficulte*15) + (deadline*10) + (3*point_git) 
                FROM STAT_MEMBRE.membre_projet WHERE id_membre = m.id AND id_projet = %s)
                WHERE m.user_github= %s
            """, (repos_id, user)
        )
        db.commit()

    db.close()


def get_stat(repos, commit_only):
    data: List = [True]
    result: Dict = {}
    page: int = 1

    # recuperation info pour le repos specifié
    info = req.get(
            f'https://api.github.com/repos/iTeam-S/{repos}?page={page}&per_page=100',
            headers={'Authorization': 'token ' + env.get('GITHUB_TOKEN')}
        ).json()
    fullname = info['full_name'],
    branch = info['default_branch']

    # parcours de chaque page, pour afficer tous les commits.
    while len(data) > 0:
        data = req.get(
            f'https://api.github.com/repos/iTeam-S/{repos}/commits?sha={branch}&page={page}&per_page=100',
            headers={'Authorization': 'token ' + env.get('GITHUB_TOKEN')}
        ).json()
        page += 1
        for commit in data:
            if not commit['author']:
                continue
            nbr_com = result.get(commit['author']['login'], {}).get('commits', 0)
            if commit['author']['login'] not in list(result.keys()):
                result[commit['author']['login']] = {} \
                    if commit_only else {'additions': 0, 'deletions': 0}
            result[commit['author']['login']]['commits'] = nbr_com+1

            if not commit_only:
                # envoie de requete pour chaque detail d'un commit.
                details = req.get(
                    commit['url'],
                    headers={'Authorization': 'token ' + env.get('GITHUB_TOKEN')}
                ).json()
                addition: int = 0
                deletion: int = 0 
                for detail in details['files']:
                    addition += detail['additions']
                    deletion += detail['deletions']
                result[commit['author']['login']]['additions'] += addition
                result[commit['author']['login']]['deletions'] += deletion
    return {
        'Nom': fullname,
        'Branch': branch,
        'Users': result
    }


@webserver.get("/{repos}")
async def stats(repos: str, commit_only: bool = False):
    '''
        API retournant le nombre de commit par utilisateur
        pour un repos donnée.
    '''
    return get_stat(repos, commit_only)


@webserver.get("/update/{repos_id}")
async def update(repos_id: int):
    """
        API utilisé pour remplir les données de point git STAT membre
    """
    proc = Thread(target=point_git, args=[repos_id])
    proc.start()
    return {
        "status": "ok"
    }



    