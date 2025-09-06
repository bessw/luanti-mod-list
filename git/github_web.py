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
            self.git_clone_url = self.repo_obj.clone_url
        else:
            raise ValueError(f"Invalid GitHub URL: {url}")

    def _get_default_branch(self):
        return self.repo_obj.default_branch

    def get_file(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        file_content = self.repo_obj.get_contents(path, ref=branch)
        return base64.b64decode(file_content.content).decode('utf-8')

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        return self.repo_obj.get_contents(path, ref=branch)

    def get_releases(self, branch=None):
        return self.repo_obj.get_releases()

    def get_issue_count(self, branch=None):
        return self.repo_obj.open_issues_count

    def get_forks(self, branch=None):
        return self.repo_obj.forks_count
