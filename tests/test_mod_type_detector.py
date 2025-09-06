import unittest
from mod_type_detector import detect_repo_type, RepoType

GAME_URL = "https://github.com/luanti-org/minetest_game"
MODPACK_URL = "https://gitlab.com/luno_luanti/lunopack_outdoors"
MOD_URL = "https://codeberg.org/Wuzzy/xdecor-libre"

class TestModTypeDetector(unittest.TestCase):
    def test_game(self):
        repo_type, metadata = detect_repo_type(GAME_URL)
        self.assertEqual(repo_type, RepoType.GAME)
        self.assertIn("name", metadata)
        self.assertIn("description", metadata)

    def test_modpack(self):
        repo_type, metadata = detect_repo_type(MODPACK_URL)
        self.assertEqual(repo_type, RepoType.MODPACK)
        self.assertIn("name", metadata)
        self.assertIn("description", metadata)

    def test_mod(self):
        repo_type, metadata = detect_repo_type(MOD_URL)
        self.assertEqual(repo_type, RepoType.MOD)
        self.assertIn("name", metadata)
        self.assertIn("description", metadata)

    def test_unknown_repo(self):
        repo_type, metadata = detect_repo_type("https://example.com/not_a_git_repo")
        self.assertEqual(repo_type, RepoType.UNKNOWN)
        self.assertEqual(metadata, {})

if __name__ == "__main__":
    unittest.main()
