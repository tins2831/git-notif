#!/usr/bin/env python3

import atexit
import git
import json
import os

from http import HTTPStatus
from http.client import HTTPSConnection, HTTPS_PORT
from sys import stderr, exit as sysexit

# the config file must always be located at
# __project_root__/.wh_config.json

BASE_DOMAIN = "discord.com"

def get_project_dir():
    git_dir = os.environ.get('GIT_DIR')

    if git_dir is None or len(git_dir) == 0:
        git_dir = '.git'

    git_loc = None
    parent_dirs = os.getcwd().split(os.sep)
    for idx, parent in enumerate(parent_dirs[::-1]):
        if parent != git_dir:
            parent_dirs.pop((len(parent_dirs) - 1))

            continue

        git_loc = os.sep + os.path.join(*parent_dirs)

    if git_loc is None:
        # we're in the project dir.
        git_loc = os.path.join(os.getcwd(), git_dir)

        if not os.path.exists(git_loc):
            print("[ - ] No .git directory found.", file = stderr)

            sysexit(1)

    return os.path.dirname(git_loc)

def _load_config():
    config_loc = os.path.join(get_project_dir(), '.wh_config.json')

    if not os.path.exists(config_loc):
        try:
            config_fobj = open(config_loc, 'w')

            config_fobj.write(json.dumps(
                {
                    'wh_id': '',
                    'wh_token': '',
                    'wh_username': '',
                    'wh_avatar_url': ''
                },
                indent = 2
            ))

            config_fobj.close()
        except Exception as e:
            print("[ - ] Failed to create the config file", file = stderr)
            print("[ - ] %s" % str(e), file = stderr)

            sysexit(1)

        print("[ - ] No config file found.", file = stderr)
        print("[ - ] New default config file made: %s" % config_loc,
            file = stderr)
        print("[ - ] Config file setup required.", file = stderr)

        sysexit(1)

    config_fobj = open(config_loc, 'r')
    config_data = json.loads(config_fobj.read())

    config_fobj.close()

    if (config_data['wh_id'] is None or
        len(config_data['wh_id']) == 0):
        print("[ - ] Config file setup required.", file = stderr)

        sysexit(1)

    if (config_data['wh_token'] is None or
        len(config_data['wh_token']) == 0):
        print("[ - ] Config file setup required.", file = stderr)

        sysexit(1)

    if (config_data['wh_username'] is None or
        len(config_data['wh_username']) == 0):
        config_data['wh_username'] = 'Git SCM'

    if (config_data['wh_avatar_url'] is None or
        len(config_data['wh_avatar_url']) == 0):
        config_data['wh_avatar_url'] = 'https://git-scm.com/images/logos/downloads/Git-Icon-1788C.png'

    return config_data

def httpcon_setup():
    httpcon = HTTPSConnection(BASE_DOMAIN, HTTPS_PORT, timeout = 10)

    atexit.register(HTTPSConnection.close, httpcon)

    return httpcon

def discord_trim(content):
    if len(content) > 1900: # 100 chars of space for other pieces of content.
        trim_msg = "\n... (trimmed)"

        content = content[:1900 - len(trim_msg)] + trim_msg

    return content

def build_req_body(config):
    repo = git.Repo(get_project_dir())
    gitcmd = git.Git(get_project_dir())

    branch = repo.active_branch
    latest_commit = None

    content = "**New commit to** **`%s`**:\n" % branch.name

    # adjust if you want different results.
    content += "**```diff\n"
    content += discord_trim(gitcmd.log('-n 1'))
    content += "\n```**"

    return json.dumps({
        'username': config['wh_username'],
        'content': content,
        'avatar_url': config['wh_avatar_url']
    })

def main(config):
    httpcon = httpcon_setup()
    httpcon.request(
        'POST',
        '/api/webhooks/' + config['wh_id'] + '/' + config['wh_token'],
        body = build_req_body(config),
        headers = {'Content-Type': 'application/json'}
    )

    resp = httpcon.getresponse()

    if resp.status != HTTPStatus.NO_CONTENT:
        print("[ - ] Server returned unrecognized http code: %d"
            % resp.status, file = stderr)
        print("[ - ] Message: '%s'" % resp.read().decode('ascii'))

        sysexit(1)

    print("[ + ] Posted webhook message.")

main(_load_config())
