from gitea import Gitea
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
                # Recognize Gitea/Forgejo by common markers
                if 'href="https://about.gitea.com/"' in text:
                    return True
                if 'href="https://forgejo.org/"' in text:
                    return True
                if 'Powered by Gitea' in text:
                    return True
                if 'codeberg.org' in url:
                    return True
        except Exception:
            pass
        return False

    def __init__(self, url, branch=None):
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        path_parts = parsed.path.strip('/').split('/')
        super().__init__(url, branch)
        if len(path_parts) >= 2:
            self.owner = path_parts[0]
            self.repo = path_parts[1]
        else:
            self.owner = None
            self.repo = None
        self.api = Gitea(self.base_url)

    def _get_default_branch(self):
        try:
            repo = self.api.repos.get_repo(self.owner, self.repo)
            return repo.default_branch
        except Exception:
            return 'main'

    def get_file(self, path, branch=None):
        # Use the Gitea Python API to get file content
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        file = self.api.repos.get_file_content(path)
        if hasattr(file, 'content') and file.encoding == 'base64':
            return base64.b64decode(file.content).decode('utf-8')
        elif hasattr(file, 'download_url'):
            file_resp = requests.get(file.download_url)
            if file_resp.status_code == 200:
                return file_resp.text
        return None

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        return self.api.repos.get_contents(self.owner, self.repo, path, ref=branch)

    def get_releases(self, branch=None):
        return self.api.repos.list_releases(self.owner, self.repo)

    def get_issue_count(self, branch=None):
        repo = self.api.repos.get_repo(self.owner, self.repo)
        return getattr(repo, 'open_issues_count', 0)

    def get_forks(self, branch=None):
        repo = self.api.repos.get_repo(self.owner, self.repo)
        return getattr(repo, 'forks_count', 0)

    def _get_clone_url(self):
        repo = self.api.repos.get_repo(self.owner, self.repo)
        return repo.clone_url
