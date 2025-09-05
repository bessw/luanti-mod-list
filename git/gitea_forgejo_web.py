import re
import requests
from urllib.parse import urlparse
from .git_web import GitWeb

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

    def _get_default_branch(self):
        if not self.owner or not self.repo:
            return 'main'
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}"
        try:
            resp = requests.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('default_branch', 'main')
        except Exception:
            pass
        return 'main'

    def get_file(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{path}?ref={branch}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            if 'content' in data:
                import base64
                return base64.b64decode(data['content']).decode('utf-8')
        return None

    def get_folder(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{path}?ref={branch}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_releases(self, branch=None):
        if not self.owner or not self.repo:
            return None
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/releases"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_issue_count(self, branch=None):
        if not self.owner or not self.repo:
            return 0
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('open_issues_count', 0)
        return 0

    def get_forks(self, branch=None):
        if not self.owner or not self.repo:
            return 0
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('forks_count', 0)
        return 0

    def _get_clone_url(self):
        if not self.owner or not self.repo:
            return None
        return f"{self.base_url}/{self.owner}/{self.repo}.git"
