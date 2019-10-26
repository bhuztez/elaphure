from dulwich.repo import Repo
from dulwich.objects import Blob, Tree, Commit
from dulwich.client import get_transport_and_path
from urllib.parse import urlparse, urlsplit
from pathlib import PurePath

class GitHubPagesWriter:

    def __init__(self, *, repo='.', branch='gh-pages', remote='origin'):
        self.repo = Repo(repo)
        self.branch = branch
        self.remote = remote
        self.tree = {}

    @property
    def base_url(self):
        config = self.repo.get_config()
        url = config.get((b'remote', self.remote.encode()), b'url')
        client, path = get_transport_and_path(url.decode())
        url = client.get_url(path)
        o = urlparse(url)
        assert o.hostname == 'github.com'
        path = o.path[1:]
        if path.endswith(".git"):
            path = path[:-4]

        user, repo = path.split('/')
        if repo == f'{user}.github.io':
            return f'https://{user}.github.io'
        else:
            return f'https://{user}.github.io/{repo}'

    def write_file(self, url, content):
        segs = PurePath(url).parts[1:]
        if url.endswith("/"):
            segs += ("index.html",)

        tree = self.tree
        for s in segs[:-1]:
            subtree = tree.get(s, {})
            tree[s] = subtree
            tree = subtree

        blob = Blob.from_string(content)
        self.repo.object_store.add_object(blob)
        tree[segs[-1]] = blob.id

    def write_tree(self, files):
        tree = Tree()
        for name, value in files.items():
            if isinstance(value, dict):
                tree.add(name.encode('utf-8'), 0o040000, self.write_tree(value))
            else:
                tree.add(name.encode('utf-8'), 0o100644, value)
        self.repo.object_store.add_object(tree)
        return tree.id

    def commit(self):
        self.write_file("/.nojekyll", b'')
        tree = self.write_tree(self.tree)
        branch = "refs/heads/" + self.branch
        commit = self.repo.do_commit(message=b'generate GitHub Pages', tree=tree, ref=branch.encode())
        self.repo[branch.encode()] = commit

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
