LexDB is a lexical cognate tracking database. It stores the full provenance of
all lexemes and cognate judgements, and allows export into a number of nexus
dialects. The database is written in the flexible python/django web framework.

LexDB is used for the Indo-European Lexical Database (IELex) at
http://ielex.mpi.nl. For more information please see the project wiki
(https://bitbucket.org/evoling/lexdb/wiki/Home) on the BitBucket development
site (https://bitbucket.org/evoling/lexdb).

For installation details and sample data see the wiki (https://bitbucket.org/evoling/lexdb/wiki/Home).

Please note that there are currently two branches of the software. The
``default`` branch will run on outdated software (Django 1.6, and doesn't
require a python newer than 2.6), and the ``py2.7-django1.8`` branch which
requires python 2.7 and Django 1.8. The commands for working with
branches are below; see also the INSTALL file in the ``py2.7-django1.8`` branch for
information about converting an older instance of the database.
  
To see which branches there are::
  
  $ hg branches
  py2.7-django1.8              762:30ec6912677a
  default                      760:eef0123ba331 (inactive)
  
To see which branch you are on::

  $ hg branch
  default

To move to another branch::

  $ hg update py2.7-django1.8
  16 files updated, 0 files merged, 26 files removed, 0 files unresolved
  
To move back::

  $ hg update default
  38 files updated, 0 files merged, 0 files removed, 0 files unresolved