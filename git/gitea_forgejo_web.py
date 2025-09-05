from gitea import Gitea, Repository
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
        
        if len(path_parts) >= 2:
            self.owner = path_parts[0]
            self.repo = path_parts[1]
        else:
            self.owner = None
            self.repo = None
        self.api = Gitea(self.base_url)
        
        # Get the Repository instance before calling super().__init__
        # since parent init calls _get_clone_url() which needs self.repository
        if self.owner and self.repo:
            self.repository = Repository.request(self.api, self.owner, self.repo)
        else:
            self.repository = None
            
        super().__init__(url, branch)

    def _get_default_branch(self):
        try:
            # Use the Repository instance to get default branch
            if self.repository:
                return self.repository.default_branch
            return 'main'
        except Exception:
            return 'main'

    def get_file(self, path, branch=None):
        # Use Repository instance to get file content
        if not self.repository:
            return None
            
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            # For file access, we need to use the internal API call since py-gitea's
            # get_file_content requires a Content object which is overly complex 
            # for our simple file path access use case
            url = f"/repos/{self.repository.owner.username}/{self.repository.name}/contents/{path}"
            params = {"ref": branch} if branch else {}
            file_info = self.api.requests_get(url, params=params)
            
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
        if not self.repository:
            return None
            
        branch = branch or getattr(self, 'branch', None) or self._get_default_branch()
        try:
            url = f"/repos/{self.repository.owner.username}/{self.repository.name}/contents/{path}"
            params = {"ref": branch} if branch else {}
            return self.api.requests_get(url, params=params)
        except Exception:
            return None

    def get_releases(self, branch=None):
        if not self.repository:
            return None
            
        try:
            url = f"/repos/{self.repository.owner.username}/{self.repository.name}/releases"
            return self.api.requests_get(url)
        except Exception:
            return None

    def get_issue_count(self, branch=None):
        if not self.repository:
            return 0
            
        try:
            # Use the Repository instance to get issue count
            return self.repository.open_issues_count
        except Exception:
            return 0

    def get_forks(self, branch=None):
        if not self.repository:
            return 0
            
        try:
            # Use the Repository instance to get forks count
            return self.repository.forks_count
        except Exception:
            return 0

    def _get_clone_url(self):
        if not self.repository:
            return None
            
        try:
            # Use the Repository instance to get clone URL
            return self.repository.clone_url
        except Exception:
            return None
