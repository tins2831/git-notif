# Git-Notif
Sends messages to a Discord webhook whenever you make a new commit to your local git repository.

### Requirements
* [GitPython](https://gitpython.readthedocs.io/en/stable/intro.html#installing-gitpython)

### Usage
Just drop [`notifier.py`](notifier.py) into your git hooks directory (by default, it's `.git/hooks`) and rename the file to `post-commit`. Update `post-commit`'s permissions to allow it to be executable: `chmod 755 post-commit`.

Optionally, you may use the following installer script to install this script automatically into your git hooks directory:
```bash
#!/usr/bin/env bash

CURL_LOC=$(which curl)

if [[ $? -ne 0 ]]; then
    if [[ -z $1 ]]; then
        echo "[ - ] Failed to locate cURL." 1>&2
        echo "[ - ] Make sure cURL is installed and available." 1>&2
        echo "[ - ] Alternatively, you may pass this script a valid location to a cURL binary as it's first argument." 1>&2
        exit 1
    fi

    if [[ $($1 -V | grep -Eo "^curl") != "curl" ]]; then
        echo "[ - ] ${1} is not a valid cURL binary." 1>&2
        exit 1
    fi

    CURL_LOC=$1
fi

if [[ -z $GIT_DIR ]]; then
    GIT_DIR=".git"
fi

# ensure we're inside a git repository.
if [[ $(find . -maxdepth 1 -type d -name $GIT_DIR -printf "%P" | tr -d "\n") != $GIT_DIR ]]; then
    echo "[ - ] No git directory found." 1>&2
    echo "[ - ] Make sure you're inside a git repository." 1>&2
    exit 1
fi

HOOKS_DIR=$(git config core.hooksPath)
if [[ -z $HOOKS_DIR ]]; then
    HOOKS_DIR=$GIT_DIR/hooks
fi

# ensure we have rw perms on the hooks dir.
if [[ ! -r $HOOKS_DIR ]] || [[ ! -w $HOOKS_DIR ]]; then
    echo "[ - ] Unable to access ${HOOKS_DIR}." 1>&2
    exit 1
fi

cd $HOOKS_DIR
$CURL_LOC https://raw.githubusercontent.com/tins2831/git-notif/master/notifier.py --output post-commit

chmod 755 post-commit

echo "[ + ] Installed."
```

There is a configuration file (`.wh_config.json`) that's generated at the project level when the tool is first ran. You must edit this file and add your webhook's ID and token:
```
https://discord.com/api/webhooks/{id}/{token}
```

### Sample
![Sample image](2021-10-29_15-00.png)
