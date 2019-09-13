import os

class FileSystemWriter:

    def __init__(self, config):
        self.basedir = os.path.abspath(config.get('path', 'output'))

    def write_file(self, url, content):
        if url.endswith('/'):
            url += 'index.html'

        filename = os.path.join(self.basedir, url[1:])
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass
