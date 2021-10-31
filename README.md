# Git-Notif
Sends messages to a Discord webhook whenever you make a new commit to your local git repository.

### Requirements
* [GitPython](https://gitpython.readthedocs.io/en/stable/intro.html#installing-gitpython)

### Usage
#### Recommended installation
Use the [`install-git-notif`](install-git-notif) installer script to install this script automatically into your git hooks directory.

#### Manual installation
Just drop [`notifier.py`](notifier.py) into your git hooks directory (by default, it's `.git/hooks`) and rename the file to `post-commit`. Update `post-commit`'s permissions to allow it to be executable: `chmod 755 post-commit`.

There is a configuration file (`.wh_config.json`) that's generated at the project level when the tool is first ran. You must edit this file and add your webhook's ID and token:
```
https://discord.com/api/webhooks/{id}/{token}
```

### Sample
![Sample image](sample.png)
