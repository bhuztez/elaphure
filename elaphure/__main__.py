import os
import sys
import argh

from .config import load_config
from .generator import scan, watch

if __name__ == '__main__':
    configfile = '.elaphure'
else:
    configfile = sys.modules['__main__'].__file__


def find_all(config):
    urls = config.urls
    for rule in urls.iter_rules():
        defaults = dict(rule.defaults or {})
        args = set(rule.arguments or ())

        for kwds in config.views[rule.endpoint].find_all(config, defaults, args):
            url = urls.build(rule.endpoint, kwds)
            if urls.match(url, return_rule=True)[0] is rule:
                yield url


def build(writer='default', config=configfile, force=False, source='default'):
    from warnings import catch_warnings
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse

    cfg = load_config(config, source)
    scan(cfg)
    client = Client(cfg.application, BaseResponse)

    with catch_warnings(record=True) as warnings:
        with cfg.writers[writer] as w:
            for url in find_all(cfg):
                w.write_file(url, client.get(url, base_url=w.base_url).data)

            for w in warnings:
                print("{}: {}".format(w.category.__name__, w.message))

            if not force and warnings:
                quit(1)


def serve(address="0.0.0.0", port=8000, config=configfile, source='default'):
    from werkzeug._reloader import run_with_reloader
    from werkzeug.serving import run_simple
    from threading import Thread

    def inner():
        cfg = load_config(config, source)
        Thread(target=lambda: watch(cfg), daemon=True).start()
        run_simple(address, port, cfg.application, use_debugger=True)

    run_with_reloader(inner)

parser = argh.ArghParser()
parser.add_commands([build, serve])
parser.dispatch()
quit()
