import requests
from urllib.parse import urlparse
from .git_web import GitWeb
import base64

class GiteaForgejoWeb(GitWeb):
    @staticmethod
    def is_gitea_or_forgejo_url(url):
        parsed = urlparse(url)
        
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
        # Call parent constructor first
        super().__init__(url, branch)
        
        # Parse URL and set owner/repo after parent init
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            self.owner = path_parts[0]
            self.repo = path_parts[1]
        else:
            self.owner = None
            self.repo = None
        
        # Cache repository info to avoid multiple API calls
        self._repo_info = None
        self._fetch_repo_info()
        self.git_clone_url = self._repo_info.get('clone_url')
    
    def _fetch_repo_info(self):
        """Fetch repository information from Gitea API"""
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            self._repo_info = response.json()

    def _get_default_branch(self):
        if self._repo_info:
            return self._repo_info.get('default_branch', 'main')
        return 'main'

    def get_file(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
            
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        # Make direct request to Gitea API
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {"ref": branch} if branch else {}
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            file_info = response.json()
            if file_info.get('encoding') == 'base64':
                content = file_info.get('content', '')
                return base64.b64decode(content).decode('utf-8')
            elif file_info.get('download_url'):
                file_resp = requests.get(file_info['download_url'], timeout=10)
                if file_resp.status_code == 200:
                    return file_resp.text
        return None

    def get_folder(self, path, branch=None):
        if not self.owner or not self.repo:
            return None
            
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {"ref": branch} if branch else {}
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None

    def get_releases(self, branch=None):
        if not self.owner or not self.repo:
            return None
        api_url = f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/releases"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None

    def get_issue_count(self, branch=None):
        if self._repo_info:
            return self._repo_info.get('open_issues_count', 0)
        return 0

    def get_forks(self, branch=None):
        if self._repo_info:
            return self._repo_info.get('forks_count', 0)
        return 0
