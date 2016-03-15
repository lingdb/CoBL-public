# CoBL

The CoBL project builds on top of the [LexDB](https://bitbucket.org/evoling/lexdb)
that is used to serve [http://ielex.mpi.nl/](http://ielex.mpi.nl/).

Deployment is currently realized with [docker](https://www.docker.com/)
as documented in [container](https://github.com/lingdb/container) repository.

## Installation

To install CoBL yourself, the following dependencies must be provided:
* A running instance of [PostgreSQL](http://www.postgresql.org/) complete with a database to use.
* Python 2.7 and pip to install the `REQUIREMENTS`.
* [Bower](http://bower.io/) to install JavaScript dependencies and bootstrap.
* [Grunt](http://gruntjs.com/) to minify JavaScript.
  * To install Grunt you'll likely need to have [node](https://nodejs.org/en/) and [npm](https://www.npmjs.com/).
  * The Grunt dependency can be omitted if you're running with `DEBUG=True`,
    because minified JavaScript will only be used when `DEBUG=False` is set.
* [git](https://git-scm.com/) to clone the repo.

To install follow these steps:
1. Make sure you've got PostgreSQL up and running with a database to use for CoBL.
2. Get hold of a recent database dump.
   If you have access to the lingdb server you will find recent ones in `/srv/container/postgres/backup` as `.bz2` files.
   Insert this dump into your database.
   If you're using the container setup you can use the [lingdb/postgres](https://github.com/lingdb/container/tree/master/postgres) container for this task.
3. Clone CoBL into a directory of your choice.
   Make sure to also provide potential submodules:
   ```
   git submodule init
   git submodule update --recursive
   ```
   This is currently used for the logo but will likely be changed in the future.
4. If you're using `virtualenvwrapper`, a command like this may be helpful:
   `mkvirtualenv -p `which python2.7` -r REQUIREMENTS CoBL`
   Basically make sure you've got the `REQUIREMENTS` installed and are using `python2.7`.
   To take advantage of development tools like the [DjDT](https://django-debug-toolbar.readthedocs.org/en/1.4/) make sure to also run
   `pip install -r REQUIREMENTS-DEV`
5. Install bower dependencies:
   Inside the `CoBL/static` directory, run: `bower install`
6. Use grunt to create minified JavaScript:
   * If you don't have grunt on your system, you can use the `CoBL/static/package.json` to provide it for you.
     Calling `npm install` should do the trick.
   Inside the `CoBL/static` directory, run: `grunt default`
7. Copy `CoBL/ielex/local_settings.py.dist` to `CoBL/ielex/local_settings.py`, and edit it.
  * Set `DEBUG` how you like it.
    If it is `True`, CoBL will serve static files itself
    and will not require the minified JavaScript so the grunt step isn't strictly necessary.
    If it is set to `False`, CoBL will use the minified JavaScript and will not provide static files itself. In this case an additional nginx to serve static files is a good choice.
  * Set the database connection settings to something like this:
    ```
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'ielexdb201510',
            'USER': 'ielexuser',
            'PASSWORD': 'rieloh7aes8ooGuu5AiPoo0dahj8ooqu',
            'HOST': 'localhost',
            'PORT': '5432',
            'ATOMIC_REQUESTS': True  # Required by sqlite3 (only)
        }
    }
    ```
  * Set `SECRET_KEY` to something secret.
8. Test that the database connection works and migrations are applied correctly:
   From `CoBL/` run:
   * `python2.7 manage.py syncdb`
   * `python2.7 manage.py migrate`
9. Run the site from `CoBL`:
   * `python2.7 manage.py runserver`
