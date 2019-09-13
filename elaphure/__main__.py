import os
import sys
import argh
from argh import arg

from .config import Config
from .static import Static
from .site import Site
from .generator import scan, watch

if __name__ == '__main__':
    configfile = '.elaphure'
else:
    configfile = sys.modules['__main__'].__file__


def generate(writer='dry-run', config=configfile, source='fs'):
    from warnings import catch_warnings
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse
    from contextlib import closing

    cfg = Config(config)
    src = cfg.SOURCES[source]
    static = Static(cfg, src)
    site = Site(cfg, src)
    scan(cfg, src)
    client = Client(static(site), BaseResponse)

    with catch_warnings(record=True) as warnings:
        with cfg.WRITERS[writer] as w:
            for url in site:
                w.write_file(url, client.get(url).data)

            for url in static:
                w.write_file(url, client.get(url).data)

            for w in warnings:
                print("{}: {}".format(w.category.__name__, w.message))

            if warnings:
                quit(1)


def serve(address="0.0.0.0", port=8000, config=configfile, source='fs'):
    from werkzeug._reloader import run_with_reloader
    from werkzeug.serving import run_simple

    def inner():
        cfg = Config(config)
        src = cfg.SOURCES[source]
        application = Static(cfg, src)(Site(cfg, src))
        watch(cfg, src)
        run_simple(address, port, application, use_debugger=True)

    run_with_reloader(inner)

parser = argh.ArghParser()
parser.add_commands([generate, serve])
parser.dispatch()
quit()
