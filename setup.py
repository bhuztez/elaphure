#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'elaphure',
    version = '0.0.4',

    url = 'https://github.com/bhuztez/elaphure',
    description = 'a static site generator',
    license = 'MIT',

    classifiers = [
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3 :: Only",
    ],

    author = 'bhuztez',
    author_email = 'bhuztez@gmail.com',

    packages = ['elaphure', 'elaphure.registries', 'elaphure.sources', 'elaphure.readers', 'elaphure.writers'],
    entry_points={
        'elaphure_extensions':
        [ 'DummyRegistry = elaphure.registries.dummy:DummyRegistry',
          'SqliteRegistry = elaphure.registries.sqlite:SqliteRegistry',
          'FileSystemSource = elaphure.sources.fs:FileSystemSource',
          'MakoView = elaphure.views.mako:MakoView',
          'MarkdownReader = elaphure.readers.markdown:MarkdownReader',
          'DryRunWriter = elaphure.writers.dry_run:DryRunWriter',
          'FileSystemWriter = elaphure.writers.fs:FileSystemWriter',
          'GitHubPagesWriter = elaphure.writers.gh_pages:GitHubPagesWriter',
        ],
        'elaphure_registries':
        [ 'default = elaphure.registries.dummy:DummyRegistry',
          'dummy = elaphure.registries.dummy:DummyRegistry',
          'sqlite = elaphure.registries.sqlite:SqliteRegistry',
        ],
        'elaphure_sources':
        [ 'default = elaphure.sources.fs:FileSystemSource',
          'fs = elaphure.sources.fs:FileSystemSource',
        ],
        'elaphure_readers':
        [ 'markdown = elaphure.readers.markdown:MarkdownReader',
        ],
        'elaphure_writers':
        [ 'default = elaphure.writers.dry_run:DryRunWriter',
          'dry_run = elaphure.writers.dry_run:DryRunWriter',
          'fs = elaphure.writers.fs:FileSystemWriter',
          'gh_pages = elaphure.writers.gh_pages:GitHubPagesWriter',
        ],
    },
    install_requires = ['argh', 'Werkzeug', 'watchdog'],
    extras_require = {
        'mako': ['Mako'],
        'markdown': ['Markdown'],
        'gh-pages': ['dulwich'],
    }
)
