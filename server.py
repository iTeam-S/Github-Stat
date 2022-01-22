from nturl2path import url2pathname
import requests as req
from fastapi import FastAPI
from typing import List, Dict
from dotenv import load_dotenv
from os import environ as env

load_dotenv()
webserver = FastAPI()


@webserver.get("/{repos}")
async def stats(repos: str):
    '''
        API retournant le nombre de commit par utilisateur
        pour un repos donnée.
    '''
    data: List = [True]
    result: Dict = {}
    page: int = 1
    info = req.get(
            f'https://api.github.com/repos/iTeam-S/{repos}?page={page}&per_page=100',
            headers={'Authorization': 'token ' + env.get('GITHUB_TOKEN')}
        ).json()
    fullname = info['full_name'],
    branch = info['default_branch']
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
            if commit['author']['login'] not in result:
                result[commit['author']['login']] = {'additions': 0, 'deletions': 0}
            result[commit['author']['login']]['commits'] = nbr_com+1

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
        'users': result
    }








