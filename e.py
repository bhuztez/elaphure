#!/usr/bin/env python3

if __name__ == '__main__':
    import elaphure.__main__

def page(filename, meta):
    slug = filename[4:-3]
    return {"type": "page",
            "title": meta.get("title", [slug])[0],
            "slug": slug}

SOURCE_FILES = [("doc/*.md", 'markdown', page)]

URLS = [
    Rule('/', defaults={'type': 'page', 'slug': 'index'}, endpoint='page'),
    Rule('/<slug>.html', defaults={'type': 'page'}, endpoint='page'),
    Rule('/static/<path:path>', endpoint='static')
]

class views(config):
    page = EntryView(template_name='templates/page.html')
    static = StaticFileView("static", ("*~",".*"))
