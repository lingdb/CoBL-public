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
  atom ielex/local_settings.py # add 'ATOMIC_REQUESTS'=True
  ./manage.py shell # test connection
  ```

## JSONfield

- `pip install django-jsonfield`

- added `data = jsonfield.JSONField()` to most models

- run:
   ```
   ./manage makemigrations --name add_JSON_fields lexicon
   ./manage migrate
   ```

- test:
  ```
  In [1]: from ielex.lexicon.models import *

  In [2]: l = Language.objects.get(id=66)

  In [3]: l
  Out[3]: <Language: Slovak>

  In [5]: l.data = {"altname":"Slovakian"}

  In [6]: l.save()

  In [7]: l.data["altname"]
  Out[7]: 'Slovakian'
  ```
