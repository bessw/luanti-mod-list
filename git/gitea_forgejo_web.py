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
        # Get the content from the specified branch, defaulting to the default branch if not provided
        branch = branch or getattr(self, 'branch', None)
        try:
            url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{path}"
            url += f"?ref={branch}" if branch else ""
            print(url)
            resp = requests.get(url)
            try:
                data = resp.json()
            except Exception:
                return None
            if isinstance(data, list):
                return None
            if data.get('encoding') == 'base64' and 'content' in data:
                return base64.b64decode(data['content']).decode('utf-8')
            elif 'download_url' in data:
                file_resp = requests.get(data['download_url'])
                if file_resp.status_code == 200:
                    return file_resp.text
            return None
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
