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


class MarkdownReader:

    def __init__(self, *,
                 extensions=['meta'],
                 extension_configs={},
                 output_format='html5',
                 tab_length=4):
        self.md = Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format=output_format,
            tab_length=tab_length)

    def metadata(self, f):
        md = self.md
        md.reset()
        lines = list(metalines(f))
        lines = NormalizeWhitespace(md).run(lines)
        lines = MetaPreprocessor(md).run(lines)
        return md.Meta

    def html(self, f):
        md = self.md
        md.reset()
        return md.convert(f.read())
