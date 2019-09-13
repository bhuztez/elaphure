class DryRunWriter:

    def __init__(self, config):
        pass

    def write_file(self, url, content):
        print("WRITE", url)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass
