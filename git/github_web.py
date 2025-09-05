from github import Github
import re
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
            self.g = Github()
            self.repo_obj = self.g.get_repo(f"{self.owner}/{self.repo}")
        else:
            raise ValueError(f"Invalid GitHub URL: {url}")

    def _get_default_branch(self):
        try:
            return self.repo_obj.default_branch
        except Exception:
            return 'master'

    def get_file(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            file_content = self.repo_obj.get_contents(path, ref=branch)
            return base64.b64decode(file_content.content).decode('utf-8')
        except Exception:
            return None

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            return self.repo_obj.get_contents(path, ref=branch)
        except Exception:
            return None

    def get_releases(self, branch=None):
        try:
            return self.repo_obj.get_releases()
        except Exception:
            return None

    def get_issue_count(self, branch=None):
        try:
            return self.repo_obj.open_issues_count
        except Exception:
            return 0

    def get_forks(self, branch=None):
        try:
            return self.repo_obj.forks_count
        except Exception:
            return 0

    def _get_clone_url(self):
        try:
            return self.repo_obj.clone_url
        except Exception:
            return None
