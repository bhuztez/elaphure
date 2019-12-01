#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'elaphure',
    version = '0.0.5',

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

    packages = ['elaphure', 'elaphure.sources', 'elaphure.readers', 'elaphure.views', 'elaphure.writers'],
    entry_points={
        'elaphure_extensions':
        [ 'FileSystemSource = elaphure.sources.fs:FileSystemSource',
          'MarkdownReader = elaphure.readers.markdown:MarkdownReader',
          'StaticFileView = elaphure.views.static:StaticFileView',
          'RawEntryView = elaphure.views.entry:RawEntryView',
          'EntryView = elaphure.views.entry:EntryView',
          'EntryListView = elaphure.views.entry:EntryListView',
          'DryRunWriter = elaphure.writers.dry_run:DryRunWriter',
          'FileSystemWriter = elaphure.writers.fs:FileSystemWriter',
          'GitHubPagesWriter = elaphure.writers.gh_pages:GitHubPagesWriter',
        ],
        'elaphure_sources':
        [ 'default = elaphure.sources.fs:FileSystemSource',
          'fs = elaphure.sources.fs:FileSystemSource',
        ],
        'elaphure_readers':
        [ 'markdown = elaphure.readers.markdown:MarkdownReader',
          'wheezy = elaphure.readers.wheezy:WheezyReader',
        ],
        'elaphure_writers':
        [ 'default = elaphure.writers.dry_run:DryRunWriter',
          'dry_run = elaphure.writers.dry_run:DryRunWriter',
          'fs = elaphure.writers.fs:FileSystemWriter',
          'gh_pages = elaphure.writers.gh_pages:GitHubPagesWriter',
        ],
    },
    install_requires = ['argh', 'Werkzeug', 'watchdog', 'wheezy.template'],
    extras_require = {
        'markdown': ['Markdown'],
        'gh-pages': ['dulwich'],
    }
)
