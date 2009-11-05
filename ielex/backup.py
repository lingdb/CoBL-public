"""Make a backup of the database using a version of the commandline

  sqlite3 db.sqlite3 .dump | bzip2 > db.dump.bz2
"""
import os
import subprocess
import bz2
import time

DB_FILE = "db.sqlite3"
BACKUP_DIR = os.path.expanduser("~/.ielex/backups")

def backup():
    # check that the backup directory exists
    try:
        os.makedirs(BACKUP_DIR)
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
