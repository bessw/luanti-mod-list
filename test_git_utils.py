"""
Unit tests for git utilities
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import our modules
from git_utils import (is_git_repository_url, check_luanti_mod_repository, 
                      _parse_mod_conf, _parse_game_conf, get_repository_info)
from db_utils import init_db

class TestGitUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up test databases in temporary files"""
        # Create temporary database files
        self.temp_dir = tempfile.mkdtemp()
        
        # Override database paths for testing
        import db_utils
        db_utils.DB_PATH = os.path.join(self.temp_dir, "test_mod_list.db")
        db_utils.FORUM_QUEUE_DB = os.path.join(self.temp_dir, "test_forum_queue.db")
        db_utils.GIT_QUEUE_DB = os.path.join(self.temp_dir, "test_git_queue.db")
        db_utils.GIT_HOSTS_DB = os.path.join(self.temp_dir, "test_git_hosts.db")
        db_utils.NON_MOD_REPOS_DB = os.path.join(self.temp_dir, "test_non_mod_repos.db")
        
        # Initialize test databases
        init_db()
    
    def tearDown(self):
        """Clean up test databases"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_is_git_repository_url(self):
        """Test git repository URL detection"""
        # Test GitHub URLs
        is_git, host_type = is_git_repository_url("https://github.com/user/repo")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "github")
        
        # Test GitLab URLs
        is_git, host_type = is_git_repository_url("https://gitlab.com/user/repo")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "gitlab")
        
        # Test Codeberg URLs
        is_git, host_type = is_git_repository_url("https://codeberg.org/user/repo")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "codeberg")
        
        # Test Bitbucket URLs
        is_git, host_type = is_git_repository_url("https://bitbucket.org/user/repo")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "bitbucket")
        
        # Test .git URLs
        is_git, host_type = is_git_repository_url("https://example.com/repo.git")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "git")
        
        # Test self-hosted GitLab
        is_git, host_type = is_git_repository_url("https://git.example.com/user/repo")
        self.assertTrue(is_git)
        self.assertEqual(host_type, "gitlab-selfhosted")
        
        # Test non-git URLs
        is_git, host_type = is_git_repository_url("https://example.com")
        self.assertFalse(is_git)
        self.assertIsNone(host_type)
        
        is_git, host_type = is_git_repository_url("https://forum.luanti.org/viewtopic.php?t=123")
        self.assertFalse(is_git)
        self.assertIsNone(host_type)
        
        # Test empty/None URLs
        is_git, host_type = is_git_repository_url("")
        self.assertFalse(is_git)
        
        is_git, host_type = is_git_repository_url(None)
        self.assertFalse(is_git)
    
    def test_parse_mod_conf(self):
        """Test mod.conf parsing"""
        mod_conf_content = '''
        # This is a comment
        name = testmod
        description = A test modification for Luanti
        author = TestAuthor
        title = Test Mod
        depends = default, farming
        optional_depends = mesecons, technic
        min_minetest_version = 5.4
        max_luanti_version = 5.9
        '''
        
        metadata = _parse_mod_conf(mod_conf_content)
        
        self.assertEqual(metadata['name'], 'testmod')
        self.assertEqual(metadata['description'], 'A test modification for Luanti')
        self.assertEqual(metadata['author'], 'TestAuthor')
        self.assertEqual(metadata['title'], 'Test Mod')
        self.assertEqual(metadata['type'], 'mod')
        self.assertEqual(metadata['depends'], ['default', 'farming'])
        self.assertEqual(metadata['optional_depends'], ['mesecons', 'technic'])
        self.assertEqual(metadata['min_version'], '5.4')
        self.assertEqual(metadata['max_version'], '5.9')
    
    def test_parse_game_conf(self):
        """Test game.conf parsing"""
        game_conf_content = '''
        # Game configuration
        name = testgame
        description = A test game for Luanti
        author = GameAuthor
        title = Test Game
        '''
        
        metadata = _parse_game_conf(game_conf_content)
        
        self.assertEqual(metadata['name'], 'testgame')
        self.assertEqual(metadata['description'], 'A test game for Luanti')
        self.assertEqual(metadata['author'], 'GameAuthor')
        self.assertEqual(metadata['title'], 'Test Game')
        self.assertEqual(metadata['type'], 'game')
    
    @patch('git_utils.requests.get')
    def test_check_luanti_mod_repository_github_mod(self, mock_get):
        """Test checking if a GitHub repository is a Luanti mod"""
        # Mock successful mod.conf response
        mod_conf_content = '''
        name = testmod
        description = A test mod
        author = testuser
        '''
        
        # Mock GitHub API response
        import base64
        encoded_content = base64.b64encode(mod_conf_content.encode()).decode()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'content': encoded_content}
        mock_get.return_value = mock_response
        
        # Test the function
        repo_url = "https://github.com/testuser/testmod"
        is_mod, metadata = check_luanti_mod_repository(repo_url)
        
        # Verify results
        self.assertTrue(is_mod)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['name'], 'testmod')
        self.assertEqual(metadata['description'], 'A test mod')
        self.assertEqual(metadata['author'], 'testuser')
        self.assertEqual(metadata['type'], 'mod')
        
        # Verify API call was made
        expected_url = "https://api.github.com/repos/testuser/testmod/contents/mod.conf"
        mock_get.assert_called_with(expected_url)
    
    @patch('git_utils.requests.get')
    def test_check_luanti_mod_repository_github_game(self, mock_get):
        """Test checking if a GitHub repository is a Luanti game"""
        game_conf_content = '''
        name = testgame
        description = A test game
        author = testuser
        '''
        
        import base64
        encoded_content = base64.b64encode(game_conf_content.encode()).decode()
        
        # Mock responses: mod.conf not found (404), game.conf found (200)
        def mock_get_side_effect(url):
            mock_response = MagicMock()
            if 'mod.conf' in url:
                mock_response.status_code = 404
            elif 'game.conf' in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {'content': encoded_content}
            else:
                mock_response.status_code = 404
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Test the function
        repo_url = "https://github.com/testuser/testgame"
        is_mod, metadata = check_luanti_mod_repository(repo_url)
        
        # Verify results
        self.assertTrue(is_mod)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['name'], 'testgame')
        self.assertEqual(metadata['description'], 'A test game')
        self.assertEqual(metadata['author'], 'testuser')
        self.assertEqual(metadata['type'], 'game')
    
    @patch('git_utils.requests.get')
    def test_check_luanti_mod_repository_github_modpack(self, mock_get):
        """Test checking if a GitHub repository is a modpack"""
        # Mock responses: mod.conf and game.conf not found, but mods/ directory exists
        def mock_get_side_effect(url):
            mock_response = MagicMock()
            if 'mod.conf' in url or 'game.conf' in url:
                mock_response.status_code = 404
            elif 'contents/mods' in url:
                mock_response.status_code = 200
                mock_response.json.return_value = [{'name': 'submod1'}, {'name': 'submod2'}]
            else:
                mock_response.status_code = 404
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Test the function
        repo_url = "https://github.com/testuser/testmodpack"
        is_mod, metadata = check_luanti_mod_repository(repo_url)
        
        # Verify results
        self.assertTrue(is_mod)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['name'], 'testmodpack')
        self.assertEqual(metadata['type'], 'modpack')
    
    @patch('git_utils.requests.get')
    def test_check_luanti_mod_repository_not_mod(self, mock_get):
        """Test checking a repository that is not a Luanti mod"""
        # Mock 404 responses for all checks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Test the function
        repo_url = "https://github.com/testuser/notamod"
        is_mod, metadata = check_luanti_mod_repository(repo_url)
        
        # Verify results
        self.assertFalse(is_mod)
        self.assertIsNone(metadata)
    
    @patch('git_utils.requests.get')
    def test_get_repository_info_github(self, mock_get):
        """Test getting GitHub repository information"""
        # Mock GitHub API response
        api_response = {
            'name': 'testmod',
            'description': 'A test modification',
            'owner': {'login': 'testuser'},
            'stargazers_count': 42,
            'forks_count': 7,
            'language': 'Lua',
            'topics': ['luanti', 'mod'],
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-12-01T00:00:00Z'
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response
        mock_get.return_value = mock_response
        
        # Test the function
        repo_url = "https://github.com/testuser/testmod"
        info = get_repository_info(repo_url)
        
        # Verify results
        self.assertEqual(info['name'], 'testmod')
        self.assertEqual(info['description'], 'A test modification')
        self.assertEqual(info['owner'], 'testuser')
        self.assertEqual(info['stars'], 42)
        self.assertEqual(info['forks'], 7)
        self.assertEqual(info['language'], 'Lua')
        self.assertEqual(info['topics'], ['luanti', 'mod'])
        
        # Verify API call was made
        expected_url = "https://api.github.com/repos/testuser/testmod"
        mock_get.assert_called_with(expected_url)
    
    @patch('git_utils.requests.get')
    def test_get_repository_info_gitlab(self, mock_get):
        """Test getting GitLab repository information"""
        # Mock GitLab API response
        api_response = {
            'name': 'testmod',
            'description': 'A test modification',
            'owner': {'username': 'testuser'},
            'star_count': 25,
            'forks_count': 5,
            'topics': ['luanti', 'mod'],
            'created_at': '2023-01-01T00:00:00Z',
            'last_activity_at': '2023-12-01T00:00:00Z'
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response
        mock_get.return_value = mock_response
        
        # Test the function
        repo_url = "https://gitlab.com/testuser/testmod"
        info = get_repository_info(repo_url)
        
        # Verify results
        self.assertEqual(info['name'], 'testmod')
        self.assertEqual(info['description'], 'A test modification')
        self.assertEqual(info['owner'], 'testuser')
        self.assertEqual(info['stars'], 25)
        self.assertEqual(info['forks'], 5)
        self.assertEqual(info['topics'], ['luanti', 'mod'])
        
        # Verify API call was made with URL encoding
        expected_url = "https://gitlab.com/api/v4/projects/testuser%2Ftestmod"
        mock_get.assert_called_with(expected_url)

if __name__ == '__main__':
    unittest.main()
