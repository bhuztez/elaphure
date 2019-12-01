import json
from warnings import warn, catch_warnings
from wheezy.template.engine import Engine
from wheezy.template.loader import FileLoader, autoreload
from wheezy.template.ext.core import CoreExtension, extends_tokens
from wheezy.template.ext.code import CodeExtension
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound

from ..database import F, MultipleEntriesReturned

if 'code' not in extends_tokens:
    extends_tokens.append('code')

class AutoRequireExtension:
    def __init__(self, *names):
        self.names = names

    @property
    def postprocessors(self):
        yield self.add_require

    def add_require(self, tokens):
        tokens.insert(0, (0, 'require', f"require({','.join(self.names)})"))

engine = Engine(
    loader=FileLoader(['.']),
    extensions=[
        CoreExtension(token_start='\\$'),
        CodeExtension(token_start='\\$'),
        AutoRequireExtension('config', 'urls', 'db', 'endpoint', 'values'),
    ])

with catch_warnings(record=True):
    engine = autoreload(engine)

engine.global_vars.update(
    {'_r': engine.render,
     'warn': warn,
     'json': json})


class Page(list):

    def __init__(self, count, page_size, page):
        self.page_size = page_size
        self.page = page
        self.count = count
        self.num_pages = self.count // page_size
        if self.count % page_size:
            self.num_pages += 1
        if not (0 < page <= self.num_pages):
            raise NotFound()

        self.has_next = page < self.num_pages
        self.has_previous = page > 1
        self.has_other_pages = page != 1

        self.start_index = (page - 1) * page_size + 1
        self.end_index = count if self.page == self.num_pages else self.start_index - 1 + page_size


DATE_FMT = {
    'year': '%Y',
    'month': '%m',
    'day': '%d',
}

def column(k):
    if '__' not in k:
        return F('json_extract(metadata, {})', f'$.{k}')
    n, a = k.split('__')
    if a in DATE_FMT:
        return F("CAST(strftime({}, json_extract(metadata, {})) AS INTEGER)", DATE_FMT[a], f'$.{n}')
    assert False

def columns(args):
    if not args:
        return F('1')
    return F(',').join(column(arg) for arg in args)


def condition(values):
    if not values:
        return F('')
    return F(
        "WHERE {}",
        F('AND').join(
            F('{} = {}', column(k), v) for k, v in values.items()))

def order_by(ordering=None):
    if ordering is None:
        return F("")

    return F(
        "ORDER BY {}",
        F(',').join(
            F("{} DESC" if key.startswith('-') else "{} ASC", column(key[1:]))
            for key in ordering.split(',')))


class BaseEntryView:
    ordering = None
    paginate_by = None
    page_kwarg = 'page'

    mimetype = 'text/html'

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def select(self, db, values):
        if not self.paginate_by:
            return db.select(
                "SELECT source.* FROM source {} {}",
                condition(values),
                order_by(self.ordering))

        page = values.pop(self.page_kwarg)
        cond = condition(values)
        count = db.execute('SELECT count(1) FROM source {}', cond).fetchone()[0]
        page = Page(count, self.paginate_by, page)
        list.__init__(
            page,
            db.select(
                'SELECT source.* FROM source {} {} LIMIT {}, {}',
                cond,
                order_by(self.ordering),
                page.start_index - 1,
                self.paginate_by))
        return page

    def get(self, db, values):
        entries = self.select(db, values)
        if not entries:
            raise NotFound()
        if len(entries) > 1:
            raise MultipleEntriesReturned()

        return entries[0]

    def find_all(self, config, values, args):
        db = config.db
        if not self.paginate_by:
            return [
                dict(zip(args, row))
                for row in db.execute(
                        "SELECT DISTINCT {} FROM source {}",
                        columns(args),
                        condition(values))]

        args.remove(self.page_kwarg)
        page = values.pop(self.page_kwarg, None)

        args = tuple(args)
        cond = condition(values)
        cols = F(',').join(column(arg) for arg in args)

        if page is None:
            if args:
                sql = F("SELECT count(1), {} FROM source {} GROUP BY {}", cols, cond, cols)
            else:
                sql = F("SELECT count(1) FROM source {}", cond)

            return [dict(zip((self.page_kwarg,) + args, [i,] + row))
                    for p, *row in db.execute(sql)
                    for i in range(1, p // self.paginate_by + bool(p % self.paginate_by) + 1)]

        count = self.paginate_by * (page - 1)

        if not args:
            sql = F("SELECT count(1) FROM source {}", cond)
            return [{self.page_kwarg: page}] if db.execute(sql).fetchone()[0] > count else []

        sql = F("SELECT {} FROM source {} GROUP BY {} HAVING count(1) > {}", cols, cond, cols, count)

        return [dict(zip((self.page_kwarg,) + args, (page,) + row))
                for row in db.execute(sql)]


class RawEntryView(BaseEntryView):

    def __call__(self, config, endpoint, values):
        return Response(self.get(config.db, values).content, mimetype=self.mimetype)


class EntryView(BaseEntryView):

    def __call__(self, config, endpoint, values):
        entry = self.get(config.db, values)

        context = {
            'config': config,
            'urls': config.urls,
            'db': config.db,
            'endpoint': endpoint,
            'values': values,
            'entry': entry,
        }

        return Response(
            engine.get_template(self.template_name).render(context),
            mimetype=self.mimetype)


class EntryListView(BaseEntryView):

    def __call__(self, config, endpoint, values):
        entries = self.select(config.db, values)

        context = {
            'config': config,
            'urls': config.urls,
            'db': config.db,
            'endpoint': endpoint,
            'values': values,
            'entries': entries,
        }

        return Response(
            engine.get_template(self.template_name).render(context),
            mimetype=self.mimetype)
