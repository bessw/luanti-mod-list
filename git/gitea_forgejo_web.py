from pygitea import Gitea
import requests
from urllib.parse import urlparse
from .git_web import GitWeb
import base64

class GiteaForgejoWeb(GitWeb):
    @staticmethod
    def is_gitea_or_forgejo_url(url):
        parsed = urlparse(url)
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                text = resp.text
                if 'href="https://about.gitea.com/"' in text:
                    return True
                if 'href="https://forgejo.org/"' in text:
                    return True
        except Exception:
            pass
        return False

    def __init__(self, url, branch=None):
        super().__init__(url, branch)
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            self.owner = path_parts[0]
            self.repo = path_parts[1]
        self.api = Gitea(self.base_url)

    def _get_default_branch(self):
        try:
            repo = self.api.repos.get_repo(self.owner, self.repo)
            return repo.default_branch or 'main'
        except Exception:
            return 'main'

    def get_file(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            file = self.api.repos.get_contents(self.owner, self.repo, path, ref=branch)
            return base64.b64decode(file.content).decode('utf-8')
        except Exception:
            return None

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            return self.api.repos.get_contents(self.owner, self.repo, path, ref=branch)
        except Exception:
            return None

    def get_releases(self, branch=None):
        try:
            return self.api.repos.list_releases(self.owner, self.repo)
        except Exception:
            return None

    def get_issue_count(self, branch=None):
        try:
            repo = self.api.repos.get_repo(self.owner, self.repo)
            return getattr(repo, 'open_issues_count', 0)
        except Exception:
            return 0

    def get_forks(self, branch=None):
        try:
            repo = self.api.repos.get_repo(self.owner, self.repo)
            return getattr(repo, 'forks_count', 0)
        except Exception:
            return 0

    def _get_clone_url(self):
        try:
            repo = self.api.repos.get_repo(self.owner, self.repo)
            return repo.clone_url
        except Exception:
            return f"{self.base_url}/{self.owner}/{self.repo}.git"
