import abc

class GitWeb(abc.ABC):
    def __init__(self, url, branch=None):
        self.url = url
        self.branch = branch
        self.owner = None
        self.repo = None
        self.git_clone_url = None

    @abc.abstractmethod
    def get_file(self, path, branch=None):
        pass

    @abc.abstractmethod
    def get_folder(self, path, branch=None):
        pass

    @abc.abstractmethod
    def get_releases(self, branch=None):
        pass

    @abc.abstractmethod
    def get_issue_count(self, branch=None):
        pass

    @abc.abstractmethod
    def get_forks(self, branch=None):
        pass

    @staticmethod
    def from_url(url, branch=None):
        from .github_web import GitHubWeb
        from .gitlab_web import GitLabWeb
        from .gitea_forgejo_web import GiteaForgejoWeb
        if GitHubWeb.is_github_url(url):
            return GitHubWeb(url, branch)
        elif GitLabWeb.is_gitlab_url(url):
            return GitLabWeb(url, branch)
        elif GiteaForgejoWeb.is_gitea_or_forgejo_url(url):
            return GiteaForgejoWeb(url, branch)
        raise ValueError(f"Unknown git server type for url: {url}")

    @staticmethod
    def is_git_server(url):
        from .github_web import GitHubWeb
        from .gitlab_web import GitLabWeb
        from .gitea_forgejo_web import GiteaForgejoWeb
        return (
            GitHubWeb.is_github_url(url) or
            GitLabWeb.is_gitlab_url(url) or
            GiteaForgejoWeb.is_gitea_or_forgejo_url(url)
        )
