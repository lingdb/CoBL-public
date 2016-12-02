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

## Handling JavaScript

CoBL uses [AMD](https://en.wikipedia.org/wiki/Asynchronous_module_definition)
with [RequireJS](http://requirejs.org/) to keep the JavaScript code organized.

For deployment the JavaScript code gets [minified](https://en.wikipedia.org/wiki/Minification_(programming)) to keep the filesize small.
We use a [hash function](https://en.wikipedia.org/wiki/Hash_function) to derive the name of the minified file.
The resulting file will have a name like `minified.af9b00f5.js` which will be specific enough so that
future changes will likely have different names and outdated browser caches won't be problematic.

Stylewise we make sure that our JavaScript code fits the expectations of [JSHint](https://en.wikipedia.org/wiki/JSHint)
to the extent that deployment will fail when code isn't formatted correctly.

Instead of tracking all our dependencies trough git directly or downloading them manually we use popular tools like [npm](https://www.npmjs.com/) and [Bower](http://bower.io/).
This makes it easy to upgrade dependencies to newer versions in the future and keeps the repository slim.

### Getting started

1. Install [node](https://nodejs.org/en/download/) together with `npm`.
2. Install `grunt` and `bower` using `npm`:
   ```shell
   npm install -g bower
   npm install -g grunt-cli
   ```
3. Install project specific `npm` dependencies:
   ```shell
   # In CoBL/static:
   npm install
   ```
4. Install project specific `bower` dependencies:
   ```shell
   # In CoBL/static:
   bower install
   ```
5. Check and minify JavaScript with `grunt`:
   ```shell
   # In CoBL/static:
   grunt
   ```
   You can also instruct `grunt` to continuously watch files for changes
   using `grunt watch` or to only use `jshint` using `grunt jshint`.
