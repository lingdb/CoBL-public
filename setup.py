from setuptools import setup, find_packages


setup(
    name='cobl',
    version='0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pastedeploy',
        'waitress',
        'bibtexparser==0.6.2',
        'clldutils',
        'configparser==3.5.0',
        'Django==1.10.4',
        'django-autocomplete-light==3.2.1',
        'django-debug-toolbar==1.6',
        'django-reversion==2.0.8',
        'django-tables2==1.2.6',
        'gunicorn==19.6.0',
        'jsonfield==1.0.3',
        'psycopg2==2.6.2',
        'python-dateutil==2.6.0',
        'requests==2.12.3',
        'six==1.10.0',
        'sqlparse==0.2.2',
        'tabulate==0.7.7',
        'WTForms==2.1',
    ],
    entry_points="""\
    [paste.app_factory]
    main = cobl:main
""")
