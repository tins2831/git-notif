#!/usr/bin/env python3

# an indicator so to know that the following messages may be related to
# git-notif.
from sys import stderr

print("[ + ] Git-Notif", file = stderr)

import atexit
import git
import json
import os

from http import HTTPStatus
from http.client import HTTPSConnection, HTTPS_PORT
from sys import exit as sysexit

# the config file must always be located at
# __project_root__/.wh_config.json

BASE_DOMAIN = "discord.com"

newer_keys = {
    'include_diff': False
}

# simple class for building valid discord form data messages.
# not flexible enough for other uses.
class DiscordFormData(object):
    boundary_name = 'boundary'

    def __init__(self, data, json_data, form_filename = '.diff'):
        if 'attachments' not in json_data:
            json_data['attachments'] = []

        json_data['attachments'].append({
            'id': len(json_data['attachments']),
            'filename': form_filename
        })

        self.json_data = json_data
        self.form_filename = form_filename
        self.data = data

        self._form_buffer = ""

    def _add_line(self, line_data):
        self._form_buffer += line_data + '\n'

    def _add_boundary(self):
        self._form_buffer += "\r\n--%s\n" % DiscordFormData.boundary_name

    def _write_data(self, data):
        self._form_buffer += '\n'
        self._form_buffer += data

    def build_form(self):
        self._add_boundary()
        self._add_line('Content-Disposition: form-data; name="payload_json"')
        self._add_line('Content-Type: application/json')
        self._write_data(json.dumps(self.json_data))

        self._add_boundary()
        self._form_buffer += 'Content-Disposition: form-data; '
        self._form_buffer += 'name="files[0]"; '
        self._form_buffer += 'filename="%s"\n' % self.form_filename
        self._add_line('Content-Type: text/x-diff')
        self._write_data(self.data)

        self._form_buffer += '\r\n--%s--' % DiscordFormData.boundary_name

        return self._form_buffer.encode('utf-8')

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
                    'wh_avatar_url': '',
                    'include_diff': False
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

    warn_keys = []
    for key in newer_keys.keys():
        if key in config_data:
            continue
        
        warn_keys.append(key)

    if len(warn_keys) > 0:
        print("[ - ] Warning: The default values for the following keys will" +
            " be used since they were not found in your config file:",
            file = stderr)
        print("[ - ] '%s'" % ', '.join(warn_keys), file = stderr)

        # set the defaults
        for key in warn_keys:
            config_data[key] = newer_keys[key]

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
    project_name = os.path.basename(get_project_dir())

    content = "**`%s`** - **New commit to `'%s'`**:\n" % (project_name,
        branch.name)

    # adjust if you want different results.
    content += "**```diff\n"
    content += discord_trim(gitcmd.log('-n 1'))
    content += "\n```**"

    json_data = {
        'username': config['wh_username'],
        'content': content,
        'avatar_url': config['wh_avatar_url']
    }

    if config['include_diff']:
        try:
            commit_history = list(repo.iter_commits())
        except ValueError as e:
            print("[ - ] Failed: %s" % str(e))

        if len(commit_history) == 1:
            commit_diff = "(No history to compare to.)"
        else:
            commit_diff = "Comparing:\n"

            commit_diff += ((' ' * 4) + commit_history[1].binsha.hex()
                + '\n')
            commit_diff += ((' ' * 4) + commit_history[0].binsha.hex()
                + '\n\n')
            commit_diff += gitcmd.diff('%s..%s' % (
                commit_history[1].binsha.hex(),
                commit_history[0].binsha.hex()
            ))

        discord_form = DiscordFormData(
            commit_diff,
            json_data = json_data
        )

        return discord_form.build_form()

    return json.dumps(json_data)

def main(config):
    httpcon = httpcon_setup()
    
    if config['include_diff']:
        headers = {
            'Content-Type': ('multipart/form-data; boundary=%s' %
                DiscordFormData.boundary_name)
        }
    else:
        headers = {'Content-Type': 'application/json'}

    httpcon.request(
        'POST',
        '/api/webhooks/' + config['wh_id'] + '/' + config['wh_token'],
        body = build_req_body(config),
        headers = headers
    )

    resp = httpcon.getresponse()

    if resp.status != HTTPStatus.NO_CONTENT and resp.status != HTTPStatus.OK:
        print("[ - ] Server returned unrecognized http code: %d"
            % resp.status, file = stderr)
        print("[ - ] Message: '%s'" % resp.read().decode('ascii'))

        sysexit(1)

    print("[ + ] Posted webhook message.")

main(_load_config())
