import gitlab
import requests
from urllib.parse import urlparse
from .git_web import GitWeb

class GitLabWeb(GitWeb):
    @staticmethod
    def is_gitlab_url(url):
        # Accept any https://<domain>/<namespace>/<repo> and check manifest.json
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            return False
        # Try to fetch manifest.json
        manifest_url = f"{parsed.scheme}://{parsed.netloc}/-/manifest.json"
        try:
            resp = requests.get(manifest_url, timeout=3)
            if resp.status_code == 200:
                manifest = resp.json()
                return manifest.get("name") == "GitLab"
        except Exception:
            pass
        return False

    def __init__(self, url, branch=None):
        super().__init__(url, branch)
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            self.owner = path_parts[0]
            self.repo = path_parts[1]
            self.base_url = f"{parsed.scheme}://{parsed.netloc}"
            self.project_path = f"{self.owner}/{self.repo}"
            self.gl = gitlab.Gitlab(self.base_url)
            self.project = self.gl.projects.get(self.project_path.replace('/', '%2F'))
        else:
            raise ValueError("URL does not contain enough path parts to determine owner and repo.")

    def _get_default_branch(self):
        try:
            return self.project.attributes.get('default_branch', 'master')
        except Exception:
            return 'master'

    def get_file(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            return f.decode('utf-8') if isinstance(f, bytes) else f
            return f.decode().decode('utf-8') if hasattr(f, 'decode') else f.decode('utf-8')
        except Exception:
            return None

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            return self.project.repository_tree(path=path, ref=branch)
        except Exception:
            return None

    def get_releases(self, branch=None):
        try:
            return self.project.releases.list()
        except Exception:
            return None

    def get_issue_count(self, branch=None):
        try:
            return self.project.attributes.get('open_issues_count', 0)
        except Exception:
            return 0

    def get_forks(self, branch=None):
        try:
            return self.project.attributes.get('forks_count', 0)
        except Exception:
            return 0

    def _get_clone_url(self):
        try:
            return self.project.attributes.get('http_url_to_repo')
        except Exception:
            return None
