"""
Crawl edX public repos to gather stats about contributions. Has a
manual blacklist of repos not to consider, mostly for third-party
forks.

Relies on a local file called github_auth that just looks like this:

    github_auth_name = 'sefk'
    github_auth_key = '4444444444444444444444444444444444444444'

Get your key from https://github.com/settings/applications, 
"Personal Access Tokens".
"""

import sys
import re
import requests
import csv
from collections import Counter, defaultdict
from requests.auth import HTTPBasicAuth
from github_auth import github_auth_name, github_auth_key
import six


github_basic_auth = HTTPBasicAuth(github_auth_name, github_auth_key)

CSVOUT_FILENAME = 'contributors.csv'
MIN_CONTRIBS = 5

MANUAL_REPO_EXCLUDES = [
    'asgard',
    'ddt',
    'django-staticfiles',
    'django-pipeline',
    'django-waffle',
    'django-wiki',
    'docker',
    'edx-mktg',
    'edx-demo-course',
    'edx-platform-private',
    'fileconveyor',
    'git-client-plugin',
    'git-plugin',
    'lettuce',
    'mako',
    'pyrasite',
    'snuggletex',
    ]

linkpat = re.compile(r'<(.*)>; rel="(.*)"')

def list_from_paged_api(url):
    """
    Make a github API call that returns a list of JSON.  Return that
    list.  If the list is paginated, iterate through pages building
    up the complete list.
    """
    result = []
    while url:
        r = requests.get(url, auth=github_basic_auth)
        page = r.json()
        print(len(page), end=" ")
        result += page
        url = ""
        if 'link' in r.headers and 'rel="next"' in r.headers['link']:
            links = r.headers['link'].split(',')
            for link in links:
                m = linkpat.match(link)
                if m and m.group(2) == "next":
                    url = m.group(1)
    print()
    return result

print("--> finding repos")
repo_full = list_from_paged_api("https://api.github.com/orgs/edx/repos")
repo_urls = [repo['contributors_url'] 
        for repo in repo_full
        if not repo['private']]

print("--> finding collaborators")
collabs = Counter()
repos = {}
for repo_url in repo_urls:
    repo = repo_url.split('/')[5]
    print("{:<5} {:<30}".format(len(collabs), repo), end=" ")
    if repo in MANUAL_REPO_EXCLUDES:
        print("skip")
        continue
    new_collabs_full = list_from_paged_api(repo_url)
    collab_contribs = []
    collab_repos = {}
    for c in new_collabs_full:
        login = c['login'].encode('ascii','ignore')
        collab_contribs.append({login: int(c['contributions'])})
        collab_repos[login] = repo
    for collab_contrib in collab_contribs:
        collabs += Counter(collab_contrib)
    for login,repo in collab_repos.items():
        if login not in repos:
            repos[login] = {repo}
        else:
            repos[login].add(repo)

print("--> for collaborators with at least {} contribs, count them and gather details"\
        .format(MIN_CONTRIBS))
total_contrib = 0
email = defaultdict(str)
company = defaultdict(str)
for login,contrib in collabs.items():
    print(f"{contrib:<5} {login:<20} ", end=" ")
    if contrib < MIN_CONTRIBS:
        print("skip")
        continue
    total_contrib += contrib
    url = f"https://api.github.com/users/{login}"
    r = requests.get(url, auth=github_basic_auth)
    user = r.json()
    if 'email' in user and user['email']:
        email[login] = user['email'].encode('ascii','ignore')
        print(email[login], end=" ")
    if 'company' in user and user['company']:
        company[login] = user['company'].encode('ascii','ignore')
        print(company[login], end=" ")
    print()

print(f"--> writing output to \"{CSVOUT_FILENAME}\"")
with open(CSVOUT_FILENAME, 'wb') as csvfile:
    writer = csv.writer(csvfile, dialect='excel', quoting=csv.QUOTE_MINIMAL)
    for login,contrib in collabs.items():
        if contrib < MIN_CONTRIBS:
            continue
        writer.writerow([
            login,
            email[login],
            company[login],
            " ".join(list(repos[login])),
            contrib,
            round(float(contrib)/float(total_contrib)*100, 1),
            ])

