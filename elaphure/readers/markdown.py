from markdown import Markdown
from markdown.preprocessors import NormalizeWhitespace
from markdown.extensions.meta import MetaPreprocessor, END_RE
from itertools import islice


def metalines(f):
    i = iter(f)
    for line in islice(i, 1):
        yield line.rstrip()

    for line in i:
        yield line.rstrip()
        if line.strip() == '' or END_RE.match(line):
            break

class Content(str):

    def __new__(self, html, attrs):
        return str.__new__(self, html)

    def __init__(self, html, attrs):
        self.__dict__.update(attrs)

class MarkdownReader:

    def __init__(self, *,
                 extensions=['meta'],
                 extension_configs={},
                 output_format='html5',
                 tab_length=4,
                 attrs=()):
        self.md = Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format=output_format,
            tab_length=tab_length)
        self.attrs = attrs

    def metadata(self, source, filename):
        md = self.md
        md.reset()
        with source.open(filename) as f:
            lines = list(metalines(f))
        lines = NormalizeWhitespace(md).run(lines)
        lines = MetaPreprocessor(md).run(lines)
        return md.Meta

    def content(self, source, filename):
        md = self.md
        md.reset()
        with source.open(filename) as f:
            data = f.read()
        html=md.convert(data)
        attrs = {a: getattr(md,a) for a in self.attrs}
        return Content(html, attrs)
