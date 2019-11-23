import os
import sys
import argh

from .config import load_config
from .static import Static
from .site import Site
from .generator import scan, watch

if __name__ == '__main__':
    configfile = '.elaphure'
else:
    configfile = sys.modules['__main__'].__file__


def build(writer='default', config=configfile, source='default'):
    from warnings import catch_warnings
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse

    cfg = load_config(config, source)
    static = Static(cfg)
    site = Site(cfg)
    scan(cfg)
    client = Client(static(site), BaseResponse)

    with catch_warnings(record=True) as warnings:
        with cfg.writers[writer] as w:
            for url in site:
                w.write_file(url, client.get(url, base_url=w.base_url).data)

            for url in static:
                w.write_file(url, client.get(url).data)

            for w in warnings:
                print("{}: {}".format(w.category.__name__, w.message))

            if warnings:
                quit(1)


def serve(address="0.0.0.0", port=8000, config=configfile, source='default'):
    from werkzeug._reloader import run_with_reloader
    from werkzeug.serving import run_simple
    from threading import Thread

    def inner():
        cfg = load_config(config, source)
        application = Static(cfg)(Site(cfg))
        Thread(target=lambda: watch(cfg), daemon=True).start()
        run_simple(address, port, application, use_debugger=True)

    run_with_reloader(inner)

parser = argh.ArghParser()
parser.add_commands([build, serve])
parser.dispatch()
quit()
