from feedgenerator import Rss201rev2Feed, Atom1Feed
from werkzeug.wrappers import Response


FEED_ARGS = (
    'items',
    'title',
    'link',
    'description',
    'language',
    'author_email',
    'author_name',
    'author_link',
    'subtitle',
    'categories',
    'feed_url',
    'feed_copyright',
    'feed_guid',
    'ttl')

class FeedView:
    Feed = None

    language = None
    author_email = None
    author_name = None
    author_link = None
    subtitle = None
    categories = None
    feed_url = None
    feed_copyright = None
    feed_guid = None
    ttl = None
    kwargs = {}
    
    def __init__(self, **kwargs):
        for name in FEED_ARGS:
            value = kwargs.pop(name, None)
            if value is not None:
                setattr(self, name, value)
        self.kwargs = kwargs

    def feed(self, endpoint, values):
        return self.Feed(
            self.title,
            self.link,
            self.description,
            self.language,
            self.author_email,
            self.author_name,
            self.author_link,
            self.subtitle,
            self.categories,
            self.feed_url,
            self.feed_copyright,
            self.feed_guid,
            self.ttl,
            **self.kwargs)

    def __call__(self, db, urls, endpoint, values, entries):
        feed = self.feed(endpoint, values)

        for item in self.items(entries):
            feed.add_item(**item)

        return Response(feed.writeString(), feed.mime_type)


class RssView:
    Feed = Rss201rev2Feed

class AtomView:
    Feed = Atom1Feed
