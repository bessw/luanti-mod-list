import unittest
from git.git_web import GitWeb

GITHUB_URL = {"url": "https://github.com/luanti-org/minetest_game", "repo_type": "game"}
GITLAB_URL = {"url": "https://gitlab.com/luno_luanti/lunopack_outdoors", "repo_type": "modpack"}
GITEA_URL = {"url": "https://codeberg.org/Wuzzy/xdecor-libre", "repo_type": "mod"}

CONF_FILES = {
    "game": "game.conf",
    "modpack": "modpack.conf",
    "mod": "mod.conf"
}

class TestGitWebByType(unittest.TestCase):
    def test_github_get_file_by_type(self):
        repo = GITHUB_URL
        gw = GitWeb.from_url(repo["url"])
        conf_file = CONF_FILES[repo["repo_type"]]
        content = gw.get_file(conf_file)
        self.assertIsNotNone(content, f"{repo['url']} should have {conf_file}")

    def test_gitlab_get_file_by_type(self):
        repo = GITLAB_URL
        gw = GitWeb.from_url(repo["url"])
        conf_file = CONF_FILES[repo["repo_type"]]
        content = gw.get_file(conf_file)
        self.assertIsNotNone(content, f"{repo['url']} should have {conf_file}")

    def test_gitea_get_file_by_type(self):
        repo = GITEA_URL
        gw = GitWeb.from_url(repo["url"])
        conf_file = CONF_FILES[repo["repo_type"]]
        content = gw.get_file(conf_file)
        self.assertIsNotNone(content, f"{repo['url']} should have {conf_file}")

    def test_non_git_repo_url(self):
        url = "https://example.com/not_a_git_repo"
        self.assertFalse(GitWeb.is_git_server(url))
        with self.assertRaises(ValueError):
            GitWeb.from_url(url)

if __name__ == "__main__":
    unittest.main()

