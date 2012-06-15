Installation Guide
========================

# Dependencies:

* [Python](http://python.org) from the 2.x series (not the 3.x series)
* Recent [Django](https://www.djangoproject.com/|) (tested on 1.3)
* Recent `[reversion]([https://github.com/etianen/django-reversion)` middleware (`easy_install django-reversion`; currently using 1.4)
* The `[south](http://south.aeracode.org/)` schema migration package (`easy_install South`; currently using 0.7.4)
* If you're going to do any work on the code, it is useful to install [debug\_toolbar](https://github.com/django-debug-toolbar/django-debug-toolbar) (`easy_install django-debug-toolbar`). If debug toolbar is available it will be activated when `DEBUG` is set to `True` in the `local_settings.py` file; see below.
* If you're going to work with the console (e.g. to import data) then is is highly desirable to install the `ipython` shell.
  
# After a clean install, 

* Run `python manage.py syncdb` from the `ielex` and add superuser when prompted (this will copy `local_settings.py.dist` to `local_settings.py` and generate a secret key)
* Customize `local_settings.py` with name of database etc. If you're doing a test then everything can be left at the default values.
** It's a good idea to move `local_settings.py` to a private, version-controlled directory _outside_ the `LexDB` hierarchy, with a symlink `ln -s ../../path/to/private_settings.py local_settings.py`. You can keep more than one version of your private settings file, e.g. one pointing to a sqlite test database and one pointing to your production server.
* Run `python manage.py migrate` to update all the database schemas to the most current version.
* Finally, do __one__ of the following:
** If you want to test the database with some sample data go to the `../dev` directory and follow the instructions in the top of the `import_csv_data.py` (this script is explained in the documentation for [importing data](https://bitbucket.org/evoling/lexdb/wiki/import_data)).
** If you want to start working in an empty database (i.e. for adding your own data), finalize the setup by running ` python manage.py lexdb_init `

To inspect the database you can use the development server. Run `./manage.py runserver` and open a browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

# Development

* The database code has some (currently not nearly enough) [unit tests](https://bitbucket.org/evoling/lexdb/wiki/unit_tests), which introduce other dependencies:
** [lxml](http://pypi.python.org/pypi/lxml/2.3.4#downloads)

