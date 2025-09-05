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

    def _get_base_and_project(self):
        parsed = urlparse(self.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if not self.owner or not self.repo:
            return None, None
        project_path = f"{self.owner}/{self.repo}"
        return base_url, project_path

    def _get_default_branch(self):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return 'master'
        api_url = f"{base_url}/api/v4/projects/{project_path.replace('/', '%2F')}"
        try:
            resp = requests.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('default_branch', 'master')
        except Exception:
            pass
        return 'master'

    def get_file(self, path, branch=None):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return None
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"{base_url}/api/v4/projects/{project_path.replace('/', '%2F')}/repository/files/{path}/raw?ref={branch}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.text
        return None

    def get_folder(self, path, branch=None):
        # Not directly supported by GitLab API, would require listing files
        return None

    def get_releases(self, branch=None):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return None
        api_url = f"{base_url}/api/v4/projects/{project_path.replace('/', '%2F')}/releases"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_issue_count(self, branch=None):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return 0
        api_url = f"{base_url}/api/v4/projects/{project_path.replace('/', '%2F')}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('open_issues_count', 0)
        return 0

    def get_forks(self, branch=None):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return 0
        api_url = f"{base_url}/api/v4/projects/{project_path.replace('/', '%2F')}"
        resp = requests.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('forks_count', 0)
        return 0

    def _get_clone_url(self):
        base_url, project_path = self._get_base_and_project()
        if not base_url or not project_path:
            return None
        return f"{base_url}/{project_path}.git"
