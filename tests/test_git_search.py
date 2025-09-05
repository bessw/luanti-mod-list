import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
import json
import sqlite3

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from git.utils import (
    is_git_repository_url, check_luanti_mod_repository,
    _is_gitlab_instance, _is_gitea_instance, _parse_mod_conf, _parse_game_conf,
    get_repository_info
)
from git.search import (
    search_github_repositories, search_gitlab_repositories, search_gitea_repositories,
    search_all_git_servers, process_git_work_queue,
    _search_github_api, _search_gitlab_api, _search_gitea_api
)


class TestGitUtils(unittest.TestCase):
    """Test git utility functions"""
    
    def test_is_git_repository_url_known_hosts(self):
        """Test recognition of known git hosting providers"""
        test_cases = [
            ("https://github.com/minetest/minetest", True, "github"),
            ("https://gitlab.com/luanti/luanti", True, "gitlab"),
            ("https://codeberg.org/user/repo", True, "codeberg"),
            ("https://bitbucket.org/user/repo", True, "bitbucket"),
            ("https://example.com/repo.git", True, "git"),
            ("https://not-a-git-site.com/page", False, None),
            ("", False, None),
            (None, False, None),
        ]
        
        for url, expected_is_git, expected_type in test_cases:
            with self.subTest(url=url):
                is_git, git_type = is_git_repository_url(url)
                self.assertEqual(is_git, expected_is_git)
                if expected_is_git:
                    self.assertEqual(git_type, expected_type)

    @patch('git.utils.requests.get')
    def test_is_gitlab_instance(self, mock_get):
        """Test GitLab instance detection"""
        # Test successful GitLab detection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "GitLab"}
        mock_get.return_value = mock_response
        
        result = _is_gitlab_instance("https://gitlab.example.com")
        self.assertTrue(result)
        mock_get.assert_called_with("https://gitlab.example.com/-/manifest.json", timeout=10)
        
        # Test non-GitLab instance
        mock_response.json.return_value = {"name": "Something Else"}
        result = _is_gitlab_instance("https://example.com")
        self.assertFalse(result)
        
        # Test connection error
        mock_get.side_effect = Exception("Connection error")
        result = _is_gitlab_instance("https://unreachable.com")
        self.assertFalse(result)

    @patch('git.utils.requests.get')
    def test_is_gitea_instance(self, mock_get):
        """Test Gitea instance detection"""
        # Test successful Gitea detection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><a title="Powered by Gitea">Gitea</a></html>'
        mock_get.return_value = mock_response
        
        result = _is_gitea_instance("https://gitea.example.com")
        self.assertTrue(result)
        
        # Test non-Gitea instance
        mock_response.text = '<html>Not a Gitea instance</html>'
        result = _is_gitea_instance("https://example.com")
        self.assertFalse(result)

    def test_parse_mod_conf(self):
        """Test mod.conf parsing"""
        mod_conf_content = '''
# This is a comment
name = test_mod
description = A test mod for Luanti
depends = default, flowers
optional_depends = farming
author = TestAuthor
title = Test Mod
min_minetest_version = 5.4.0
max_luanti_version = 5.9.0
        '''.strip()
        
        metadata = _parse_mod_conf(mod_conf_content)
        
        self.assertEqual(metadata['name'], 'test_mod')
        self.assertEqual(metadata['description'], 'A test mod for Luanti')
        self.assertEqual(metadata['depends'], ['default', 'flowers'])
        self.assertEqual(metadata['optional_depends'], ['farming'])
        self.assertEqual(metadata['author'], 'TestAuthor')
        self.assertEqual(metadata['title'], 'Test Mod')
        self.assertEqual(metadata['min_version'], '5.4.0')
        self.assertEqual(metadata['max_version'], '5.9.0')
        self.assertEqual(metadata['type'], 'mod')

    def test_parse_game_conf(self):
        """Test game.conf parsing"""
        game_conf_content = '''
name = test_game
description = A test game for Luanti
author = GameAuthor
title = Test Game
        '''.strip()
        
        metadata = _parse_game_conf(game_conf_content)
        
        self.assertEqual(metadata['name'], 'test_game')
        self.assertEqual(metadata['description'], 'A test game for Luanti')
        self.assertEqual(metadata['author'], 'GameAuthor')
        self.assertEqual(metadata['title'], 'Test Game')
        self.assertEqual(metadata['type'], 'game')

    @patch('git.utils.requests.get')
    def test_check_luanti_mod_repository_github(self, mock_get):
        """Test checking if a GitHub repository is a Luanti mod"""
        # Mock successful mod.conf fetch
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': 'bmFtZSA9IHRlc3RfbW9kCmRlc2NyaXB0aW9uID0gQSB0ZXN0IG1vZA=='  # base64 encoded "name = test_mod\ndescription = A test mod"
        }
        mock_get.return_value = mock_response
        
        is_mod, metadata = check_luanti_mod_repository("https://github.com/user/test_mod")
        
        self.assertTrue(is_mod)
        self.assertEqual(metadata['name'], 'test_mod')
        self.assertEqual(metadata['description'], 'A test mod')
        self.assertEqual(metadata['type'], 'mod')

    @patch('git.utils.requests.get')
    def test_check_luanti_mod_repository_not_mod(self, mock_get):
        """Test checking repository that is not a Luanti mod"""
        # Mock 404 response for mod.conf
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        is_mod, metadata = check_luanti_mod_repository("https://github.com/user/not_a_mod")
        
        self.assertFalse(is_mod)
        self.assertIsNone(metadata)

    @patch('git.utils.requests.get')
    def test_get_repository_info_github(self, mock_get):
        """Test getting GitHub repository information"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test_repo',
            'description': 'A test repository',
            'owner': {'login': 'testuser'},
            'stargazers_count': 42,
            'forks_count': 10,
            'language': 'Lua',
            'topics': ['minetest', 'luanti'],
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-12-01T00:00:00Z'
        }
        mock_get.return_value = mock_response
        
        info = get_repository_info("https://github.com/testuser/test_repo")
        
        self.assertEqual(info['name'], 'test_repo')
        self.assertEqual(info['description'], 'A test repository')
        self.assertEqual(info['owner'], 'testuser')
        self.assertEqual(info['stars'], 42)
        self.assertEqual(info['forks'], 10)
        self.assertEqual(info['language'], 'Lua')
        self.assertEqual(info['topics'], ['minetest', 'luanti'])


class TestGitSearch(unittest.TestCase):
    """Test git search functionality"""
    
    @patch('git.search.requests.get')
    @patch('git.search.time.sleep')
    def test_search_github_api(self, mock_sleep, mock_get):
        """Test GitHub API search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'html_url': 'https://github.com/user/mod1',
                    'name': 'mod1',
                    'description': 'A test mod',
                    'stargazers_count': 10,
                    'forks_count': 5,
                    'language': 'Lua',
                    'owner': {'login': 'user'},
                    'topics': ['minetest']
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        repos = _search_github_api("minetest", 10)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'mod1')
        self.assertEqual(repos[0]['url'], 'https://github.com/user/mod1')
        self.assertEqual(repos[0]['stars'], 10)

    @patch('git.search.requests.get')
    @patch('git.search.time.sleep')
    def test_search_gitlab_api(self, mock_sleep, mock_get):
        """Test GitLab API search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'web_url': 'https://gitlab.com/user/mod1',
                'name': 'mod1',
                'description': 'A test mod',
                'star_count': 15,
                'forks_count': 3,
                'namespace': {'name': 'user'},
                'topics': ['luanti']
            }
        ]
        mock_get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        repos = _search_gitlab_api("https://gitlab.com", "luanti", 10)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'mod1')
        self.assertEqual(repos[0]['url'], 'https://gitlab.com/user/mod1')
        self.assertEqual(repos[0]['stars'], 15)

    @patch('git.search.requests.get')
    @patch('git.search.time.sleep')
    def test_search_gitea_api(self, mock_sleep, mock_get):
        """Test Gitea API search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'html_url': 'https://gitea.example.com/user/mod1',
                    'name': 'mod1',
                    'description': 'A test mod',
                    'stars_count': 8,
                    'forks_count': 2,
                    'language': 'Lua',
                    'owner': {'login': 'user'},
                    'topics': ['minetest']
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        repos = _search_gitea_api("https://gitea.example.com", "minetest", 10)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'mod1')
        self.assertEqual(repos[0]['url'], 'https://gitea.example.com/user/mod1')
        self.assertEqual(repos[0]['stars'], 8)

    @patch('git.search.search_github_repositories')
    @patch('git.search.get_all_git_hosts')
    @patch('git.search.add_to_git_queue')
    @patch('git.search.is_git_repo_in_queue')
    def test_search_all_git_servers(self, mock_is_in_queue, mock_add_to_queue, 
                                   mock_get_hosts, mock_search_github):
        """Test searching all git servers"""
        # Mock GitHub search results
        mock_search_github.return_value = [
            {
                'url': 'https://github.com/user/mod1',
                'name': 'mod1',
                'description': 'Test mod',
                'stars': 10,
                'language': 'Lua'
            }
        ]
        
        # Mock git hosts (empty for this test)
        mock_get_hosts.return_value = []
        
        # Mock queue operations
        mock_is_in_queue.return_value = False
        mock_add_to_queue.return_value = True
        
        repos = search_all_git_servers(['luanti', 'minetest'], 50)
        
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'mod1')
        mock_search_github.assert_called_once()
        mock_add_to_queue.assert_called_once()

    @patch('git.search.get_next_git_repos_from_queue')
    @patch('git.search.mark_git_repo_processed')
    @patch('git.utils.check_luanti_mod_repository')
    @patch('db_utils.add_mod_to_db')
    def test_process_git_work_queue(self, mock_add_mod, mock_check_mod, 
                                   mock_mark_processed, mock_get_repos):
        """Test processing git work queue"""
        # Mock repository data from queue
        mock_get_repos.return_value = [
            (1, 'https://github.com/user/mod1', 'github_search', '{"name": "mod1"}'),
            (2, 'https://github.com/user/not_mod', 'github_search', '{"name": "not_mod"}')
        ]
        
        # Mock mod checking results
        def check_mod_side_effect(url):
            if 'mod1' in url:
                return True, {'name': 'mod1', 'type': 'mod', 'description': 'Test mod'}
            else:
                return False, None
        
        mock_check_mod.side_effect = check_mod_side_effect
        mock_add_mod.return_value = 'added'
        
        # Import and call the function (avoiding circular import)
        from git.search import process_git_work_queue
        process_git_work_queue(2)
        
        # Verify mocks were called correctly
        mock_get_repos.assert_called_once_with(2)
        self.assertEqual(mock_check_mod.call_count, 2)
        mock_add_mod.assert_called_once()  # Only called for mod1
        self.assertEqual(mock_mark_processed.call_count, 2)  # Both repos marked as processed

    @patch('git.search.requests.get')
    def test_search_github_repositories_rate_limiting(self, mock_get):
        """Test that rate limiting is applied"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        mock_get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        with patch('git.search.time.sleep') as mock_sleep:
            search_github_repositories(['luanti', 'minetest'], 10)
            # Should sleep between requests
            mock_sleep.assert_called()

    def test_search_github_repositories_deduplication(self):
        """Test that duplicate repositories are removed"""
        with patch('git.search._search_github_api') as mock_search:
            # Mock returning duplicate repositories
            mock_search.side_effect = [
                [
                    {'url': 'https://github.com/user/mod1', 'name': 'mod1'},
                    {'url': 'https://github.com/user/mod2', 'name': 'mod2'}
                ],
                [
                    {'url': 'https://github.com/user/mod1', 'name': 'mod1'},  # Duplicate
                    {'url': 'https://github.com/user/mod3', 'name': 'mod3'}
                ]
            ]
            
            with patch('git.search.time.sleep'):
                repos = search_github_repositories(['luanti', 'minetest'], 10)
            
            # Should have 3 unique repositories
            self.assertEqual(len(repos), 3)
            urls = [repo['url'] for repo in repos]
            self.assertEqual(len(set(urls)), 3)  # All unique


class TestGitWorkQueue(unittest.TestCase):
    """Test git work queue functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = 'test_git_queue.db'
        # Create test database
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE git_work_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                metadata TEXT,
                processed INTEGER DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_date TIMESTAMP,
                error TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    @patch('git.search.sqlite3.connect')
    def test_get_next_git_repos_from_queue(self, mock_connect):
        """Test getting next repositories from work queue"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            (1, 'https://github.com/user/mod1', 'github_search', '{"name": "mod1"}'),
            (2, 'https://github.com/user/mod2', 'github_search', '{"name": "mod2"}')
        ]
        
        from git.search import get_next_git_repos_from_queue
        repos = get_next_git_repos_from_queue(2)
        
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0][1], 'https://github.com/user/mod1')
        mock_cursor.execute.assert_called_once()

    @patch('git.search.sqlite3.connect')
    def test_mark_git_repo_processed(self, mock_connect):
        """Test marking repository as processed"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        from git.search import mark_git_repo_processed
        mark_git_repo_processed(1, "Test error")
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
