#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'elaphure',
    version = '0.0.3',

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

    packages = ['elaphure', 'elaphure.sources', 'elaphure.readers', 'elaphure.writers'],
    entry_points={
        'elaphure_sources':
        [ 'fs = elaphure.sources.fs:FileSystemSource' ],
        'elaphure_readers':
        [ 'markdown = elaphure.readers.markdown:MarkdownReader' ],
        'elaphure_writers':
        [ 'dry-run = elaphure.writers.dry_run:DryRunWriter',
          'fs = elaphure.writers.fs:FileSystemWriter',
          'gh-pages = elaphure.writers.gh_pages:GitHubPagesWriter' ],
    },
    install_requires = ['argh', 'Werkzeug', 'watchdog', 'Mako'],
    extras_require = {
        'markdown': ['Markdown'],
        'gh-pages': ['dulwich'],
    }
)
