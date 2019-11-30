import os
from datetime import datetime
from watchdog.events import FileSystemEventHandler


class Handler(FileSystemEventHandler):

    def __init__(self, queue):
        self.queue = queue

    def dispatch(self, event):
        if event.is_directory:
            return
        return super().dispatch(event)

    def on_created(self, event):
        self.queue.put(("created", event.src_path))

    def on_deleted(self, event):
        self.queue.put(("deleted", event.src_path))

    def on_modified(self, event):
        self.queue.put(("modified", event.src_path))

    def on_moved(self, event):
        self.queue.put(("moved", event.src_path, event.dest_path))


class FileSystemSource:

    def __init__(self, basedir='.'):
        self.basedir = os.path.abspath(basedir)

    def walk(self, base=''):
        base = os.path.join(self.basedir, base)
        for root, dirs, files in os.walk(base):
            for name in files:
                yield os.path.relpath(os.path.join(root, name), self.basedir)

    def open(self, filename, mode='r'):
        return open(os.path.join(self.basedir, filename), mode)

    def watch(self):
        from queue import Queue
        from watchdog.observers import Observer

        queue = Queue()
        observer = Observer()
        observer.schedule(Handler(queue), self.basedir, recursive=True)
        observer.start()

        try:
            for filename in self.walk():
                yield ("created", filename)

            while True:
                event = queue.get()
                yield (event[0],) + tuple(
                    os.path.relpath(p, self.basedir) for p in event[1:])
        finally:
            observer.stop()
            observer.join()
