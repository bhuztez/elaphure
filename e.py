#!/usr/bin/env python3

if __name__ == '__main__':
    import elaphure.__main__

def page(filename, meta):
    slug = filename[6:-3]
    return {"type": "page",
            "title": meta.get("title", [slug])[0],
            "tags": meta.get("tag", []),
            "slug": slug}

SOURCE_FILES = [("pages/*.md", 'markdown', page)]

URLS = [Rule('/<slug>.html', defaults={'type': 'page'}, endpoint='page')]

class registries(config):
    default = DummyRegistry()

class HTMLView(MakoView):
    template_dirs = ['templates']

class views(config):
    page = HTMLView('page.html')
