# Git-Notif
Sends messages to a Discord webhook whenever there is a new commit in your local git repository.

### Usage
Just drop [`notifier.py`](notifier.py) into your git hooks directory (by default, it's `.git/hooks`) and rename the file to `post-commit`. Update `post-commit`'s permissions to allow it to be executable: `chmod 755 post-commit`.

### Sample
![Sample image](2021-10-29_15-00.png)
