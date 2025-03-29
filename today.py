import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']

def format_plural(unit):
    return 's' if unit != 1 else ''

def daily_readme(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')

def simple_request(query, variables):
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
    if request.status_code == 200:
        return request
    raise Exception('GraphQL error', request.status_code, request.text)

def get_commit_count():
    query = '''
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    res = simple_request(query, variables).json()
    return res['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']

def get_repos_and_stars():
    query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER, first: 100) {
                totalCount
                nodes {
                    stargazerCount
                }
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    res = simple_request(query, variables).json()
    repos = res['data']['user']['repositories']['totalCount']
    stars = sum(repo['stargazerCount'] for repo in res['data']['user']['repositories']['nodes'])
    return repos, stars

def get_followers():
    query = '''
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    res = simple_request(query, variables).json()
    return res['data']['user']['followers']['totalCount']

def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, follower_data):
    tree = etree.parse(filename)
    root = tree.getroot()

    def set_text(id, value):
        el = root.find(".//*[@id='{}']".format(id))
        if el is not None:
            el.text = str(value)

    def set_dots(id, value, length):
        dots = '.' * max(0, length - len(str(value)))
        el = root.find(".//*[@id='{}']".format(id))
        if el is not None:
            el.text = ' ' + dots + ' ' if dots else ''

    set_text('age_data', age_data)
    set_dots('age_data_dots', age_data, 22)
    set_text('commit_data', commit_data)
    set_dots('commit_data_dots', commit_data, 22)
    set_text('star_data', star_data)
    set_dots('star_data_dots', star_data, 14)
    set_text('repo_data', repo_data)
    set_dots('repo_data_dots', repo_data, 6)
    set_text('follower_data', follower_data)
    set_dots('follower_data_dots', follower_data, 10)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    age = daily_readme(datetime.datetime(1996, 4, 3))
    commit_count = get_commit_count()
    repos, stars = get_repos_and_stars()
    followers = get_followers()
    svg_overwrite('light_mode.svg', age, commit_count, stars, repos, followers)
    svg_overwrite('dark_mode.svg', age, commit_count, stars, repos, followers)