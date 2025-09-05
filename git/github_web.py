import re
import requests
import base64
from .git_web import GitWeb

class GitHubWeb(GitWeb):
    @staticmethod
    def is_github_url(url):
        return re.match(r'https://github\.com/[\w\-\.]+/[\w\-\.]+/?$', url)

    def __init__(self, url, branch=None):
        super().__init__(url, branch)
        match = re.match(r'https://github\.com/([\w\-\.]+)/([\w\-\.]+)/?', url)
        if match:
            self.owner, self.repo = match.groups()

    def _get_default_branch(self):
        if not self.owner or not self.repo:
            return 'master'
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        try:
            resp = requests.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('default_branch', 'master')
        except Exception:
            pass
        return 'master'

    def get_file(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}?ref={branch}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            if 'content' in data:
                return base64.b64decode(data['content']).decode('utf-8')
        return None

    def get_folder(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}?ref={branch}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_releases(self, branch=None):
        if not self.owner or not self.repo:
            return None
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_issue_count(self, branch=None):
        if not self.owner or not self.repo:
            return 0
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('open_issues_count', 0)
        return 0

    def get_forks(self, branch=None):
        if not self.owner or not self.repo:
            return 0
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('forks_count', 0)
        return 0

    def _get_clone_url(self):
        if not self.owner or not self.repo:
            return None
        return f"https://github.com/{self.owner}/{self.repo}.git"
