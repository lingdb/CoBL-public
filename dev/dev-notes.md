# Development notes

## Upgrade

- Made a postgres database with 201510 data

- First:
  ```
  createdb -T template0 -O ielexuser ielexdb201510
  psql ielexdb201510 < ~/Dropbox/IELex-data/ielexdb.dump_2015-10-13.sql
  cd IELex-dev/
  workon ems06
  atom ielex/local_settings.py # fix connection settings
  ./manage.py shell # test connection
  ```
-  Then:
  ```
  workon py2.7-django1.8
  hg update py2.7-django1.8
  ./manage.py migrate --fake
  atom ielex/local_settings.py # add 'ATOMIC_REQUESTS':True
  ./manage.py shell # test connection
  ```

## JSONfield

- `pip install django-jsonfield`

- added `data = jsonfield.JSONField()` to most models; for Language table named
  it `altname` instead

- run:
   ```
   ./manage.py makemigrations --name add_JSON_fields lexicon
   ./manage.py migrate
   ```

- test:
  ```
  In [1]: from ielex.lexicon.models import *

  In [2]: l = Language.objects.get(ascii_name="Dutch")

  In [3]: l
  Out[3]: <Language: Dutch>

  In [4]: l.altname = {"Dyen":"Dutch_List"}

  In [5]: l.save()

  In [6]: l.altname["Dyen"]
  Out[6]: 'Dutch_List'
  ```
