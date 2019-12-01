Title: Quickstart

## Requirements

 * Python 3.7+

## Installation

Run the following command to install elaphure

    pip3 install elaphure[markdown]

## Create configuration file

create a file named `e.py` with the following content


    #!/usr/bin/env python3

    if __name__ == '__main__':
        import elaphure.__main__


## Preview your site

run the following command

    python3 e.py serve

open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser,
you will see a page titled "404 Not Found".

## Create first view

Elaphure uses [werkzeug](https://werkzeug.palletsprojects.com/en/0.16.x/routing/) for URL routing.

    URLS = [
        Rule('/', defaults={'type': 'article'}, endpoint='article_list'),
    ]

Pass `{'type': 'article'}` to `EntryListView`, thus it will retrieve all the entries whose `type` is `'article'` from database

    class views(config):
        article_list = EntryListView(template_name='article_list.html')

Elaphure uses [Wheezy Template](https://pythonhosted.org/wheezy.template/userguide.html) to generate HTML.

Create a file named `article_list.html` with the following content

    $require(entries)

    <ul>
    $for entry in entries:
    <li>$entry["title"]</li>
    $endfor
    </ul>

Since no article had been created, open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) now, you will see an empty page.

## Create an article

To add an article to the database, elaphure has to know where to find source files.

    def article(filename, meta):
        slug = filename[:-3]
        return {"type": "article",
                "title": meta.get("title", [slug])[0],
                "slug": slug}

    SOURCE_FILES = [("*.md", 'markdown', article)]

Create a file named `foo.md` with following content

    Title: My First Article

    Foo

open [http://127.0.0.1:8000/](http://127.0.0.1:8000/), you will see a page with following content

> * My First Article

## Create a view to show the article

As with `EntryListView`, when visiting [http://127.0.0.1:8000/foo.html](http://127.0.0.1:8000/foo.html), `EntryView` will retrieve from database the entry whose `type` is `'article'` and `slug` is `'foo'`.

    class views(config):
        article_list = EntryListView(template_name='article_list.html')
        article = EntryView(template_name='article.html')

    URLS = [
        Rule('/', defaults={'type': 'article'}, endpoint='article_list'),
        Rule('/<slug>.html', defaults={'type': 'article'}, endpoint='article')
    ]

Create a file named `article.html` with the following content

    $require(entry)

    <h1>$entry["title"]</h1>

    $entry.content

open [http://127.0.0.1:8000/foo.html](http://127.0.0.1:8000/foo.html), you will see a page with following content:

> ### My First Article
> Foo

## Add link to the article

change the content of `article_list.html` to the following

    $require(entries)

    <ul>
    $for entry in entries:
    <li><a href="$urls.build('article', {'slug': entry['slug']})">$entry["title"]</a></li>
    $endfor
    </ul>

open [http://127.0.0.1:8000/](http://127.0.0.1:8000/), you will see a page with following content

> * [My First Article](http://127.0.0.1:8000/foo.html)
