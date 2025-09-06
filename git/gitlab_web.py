import gitlab
import requests
import base64
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
        resp = requests.get(manifest_url, timeout=3)
        if resp.status_code == 200:
            manifest = resp.json()
            return manifest.get("name") == "GitLab"
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
            self.project = self.gl.projects.get(self.project_path)
            self.git_clone_url = self.project.attributes.get('http_url_to_repo')
        else:
            raise ValueError("URL does not contain enough path parts to determine owner and repo.")

    def _get_default_branch(self):
        return self.project.attributes.get('default_branch', 'master')

    def get_file(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        f = self.project.files.get(file_path=path, ref=branch)
        return base64.b64decode(f.content).decode('utf-8')

    def get_folder(self, path, branch=None):
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        return self.project.repository_tree(path=path, ref=branch)

    def get_releases(self, branch=None):
        return self.project.releases.list()

    def get_issue_count(self, branch=None):
        return self.project.attributes.get('open_issues_count', 0)

    def get_forks(self, branch=None):
        return self.project.attributes.get('forks_count', 0)
