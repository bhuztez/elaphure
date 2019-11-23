# Elaphure

Elaphure is a static site generator inspired by the LAMP stack which
commonly used to run dynamic websites. And Elaphure uses an in-memory
SQLite database, and mostly rely on its JSON1 extension.

## Getting Started

The most important concept of elaphure is the database. All the pages
are generated from metadata stored there.

Metadata is collected from files that match one of the patterns in
`SOURCE_FILES`.

For example, with following configuration, when elaphure found
`pages/foo.md`, it would add to the database `{"type": "page", "slug":
"foo"}`

```python3
def page(filename, meta):
    slug = filename[6:-3]
    return {"type": "page",
            "slug": slug}

SOURCE_FILES = [("pages/*.md", 'markdown', page)]
```

Define `URLS` defined like the following in your config file

```python3
URLS = [Rule('/<slug>.html', defaults={'type': 'page'}, endpoint='page')]
```

When you visit `/foo.html`, elaphure will try to find out the entry
whose `type` is `page` and `slug` is `foo`, and use `page` view to
generate the output.

```python3
class views(config):
    page = WheezyView('templates/page.html')
```

Also Elaphure would pass the markdown metadata to the `meta` argument
of the `page` function.

put all together, and save it to `e.py`

```python3
#!/usr/bin/env python3

if __name__ == '__main__':
    import elaphure.__main__

TEMPLATE_DIRS = ['templates']

def page(filename, meta):
    slug = filename[6:-3]
    return {"type": "page",
            "slug": slug}

SOURCE_FILES = [("pages/*.md", 'markdown', page)]

URLS = Map([Rule('/<slug>.html', defaults={'type': 'page'}, endpoint='page')])

class views(config):
    page = WheezyView('templates/page.html')
```

run `python3 e.py serve` and visit `http://127.0.0.1:8000/foo.html`

## Tagging

Now, add tagging to the static site.

Change `foo.md` to

```
Title: Foo
Tag: bar

foo
```

Add `bar.md`

```
Title: Bar

bar
```

Modify the `page` function

```python3
def page(filename, meta):
    slug = filename[6:-3]
    return {"type": "page",
            "title": meta.get("title", [slug])[0],
            "tags": meta.get("tag", []),
            "slug": slug}
```

To get all the pages tagging with current page's slug, add this to `page.html`

```
%(
pages = [
  page
  for page in db.select({"type": "page"})
  if entry["slug"] in page.get("tags", [])]
)
%if pages:
<hr/>
<h4>Pages tagged with "%entry["title"]"</h4>
<ul>
%for page in pages:
<li><a href="%urls.build('page', {'slug': page['slug']})">%page["title"]</a></li>
%end
</ul>
%end
```

And then visit `http://127.0.0.1:8000/bar.html`
