"""Make a backup of the database using a version of the commandline

  sqlite3 db.sqlite3 .dump | bzip2 > db.dump.bz2
"""
import os
import subprocess
import bz2
import time
import hashlib
from ielex import settings

DB_FILE = "db.sqlite3"

# insert the md5 hash of the secret key into the backup path (so that multiple
# databases can be saved under the same hierarchy (plus put a soft link using
# the short name - in case of name collisions the most recent version will the
# the link, which is probably the right behaviour)

def backup():
    # check that the backup directory exists
    try:
        BACKUP_DIR = os.path.join(os.path.expanduser("~/.ielex/backups"),
                hashlib.md5(settings.SECRET_KEY).hexdigest())
        os.makedirs(BACKUP_DIR)
        os.symlink(BACKUP_DIR, os.path.join(os.path.expanduser("~/.ielex/backups"),
                settings.project_short_name))
    except OSError:
        pass

    start_time = time.time()
    filename = "db.dump.%s.bz2" % time.strftime("%y-%m-%d_%H-%M-%S",
            time.localtime())
    # dump data and compress it to file
    output, error = subprocess.Popen(["sqlite3", "db.sqlite3",
            ".dump"], stdout=subprocess.PIPE).communicate()
    data = bz2.compress(output)
    backup_file = file(os.path.join(BACKUP_DIR, filename), "wb")
    backup_file.write(data)
    backup_file.close()

    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    msg = "Backed up database to file %s in directory %s (elapsed time %02d:%02d)" %\
            (filename, BACKUP_DIR, minutes, seconds)
    return msg

if __name__ == "__main__":
    backup()
