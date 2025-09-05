from gitea import Gitea
import requests
from urllib.parse import urlparse
from .git_web import GitWeb
import base64

class GiteaForgejoWeb(GitWeb):
    @staticmethod
    def is_gitea_or_forgejo_url(url):
        parsed = urlparse(url)
        # Known Gitea/Forgejo instances
        if 'codeberg.org' in url:
            return True
        
        # Try to detect by making a request to the base URL
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        try:
            resp = requests.get(base_url, timeout=5)
            if resp.status_code == 200:
                text = resp.text
                # Recognize Gitea/Forgejo by common markers
                if 'href="https://about.gitea.com/"' in text:
                    return True
                if 'href="https://forgejo.org/"' in text:
                    return True
                if 'Powered by Gitea' in text:
                    return True
                if 'Powered by Forgejo' in text:
                    return True
                # Check for meta generator tag
                if 'content="Gitea"' in text or 'content="Forgejo"' in text:
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
            # Use direct API call to get repository info
            repo_info = self.api.requests_get(f"/repos/{self.owner}/{self.repo}")
            return repo_info.get('default_branch', 'main')
        except Exception:
            return 'main'

    def get_file(self, path, branch=None):
        # Use direct API call to get file content
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            file_info = self.api.requests_get(f"/repos/{self.owner}/{self.repo}/contents/{path}", params={"ref": branch})
            if file_info.get('encoding') == 'base64':
                content = file_info.get('content', '')
                return base64.b64decode(content).decode('utf-8')
            elif file_info.get('download_url'):
                file_resp = requests.get(file_info['download_url'])
                if file_resp.status_code == 200:
                    return file_resp.text
        except Exception:
            pass
        return None

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            return self.api.requests_get(f"/repos/{self.owner}/{self.repo}/contents/{path}", params={"ref": branch})
        except Exception:
            return None

    def get_releases(self, branch=None):
        try:
            return self.api.requests_get(f"/repos/{self.owner}/{self.repo}/releases")
        except Exception:
            return None

    def get_issue_count(self, branch=None):
        try:
            repo_info = self.api.requests_get(f"/repos/{self.owner}/{self.repo}")
            return repo_info.get('open_issues_count', 0)
        except Exception:
            return 0

    def get_forks(self, branch=None):
        try:
            repo_info = self.api.requests_get(f"/repos/{self.owner}/{self.repo}")
            return repo_info.get('forks_count', 0)
        except Exception:
            return 0

    def _get_clone_url(self):
        try:
            repo_info = self.api.requests_get(f"/repos/{self.owner}/{self.repo}")
            return repo_info.get('clone_url')
        except Exception:
            return None
