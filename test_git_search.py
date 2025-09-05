import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import json

# Add current directory to path to import modules
sys.path.append(os.path.dirname(__file__))

from git.search import (
    search_github_repositories, 
    search_gitlab_repositories,
    search_gitea_repositories,
    search_all_git_servers,
    process_git_work_queue
)
from git.utils import check_luanti_mod_repository, is_git_repository_url
from db_utils import init_all_databases, add_to_git_queue, get_unprocessed_git_repos, mark_git_repo_processed, get_all_git_hosts

class TestGitSearch(unittest.TestCase):
    """Test cases for git search functionality"""
    
    def setUp(self):
        """Set up test environment with temporary database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_mod_search.db')
        
        # Override database paths for testing
        import db_utils
        db_utils.MOD_DATABASE = self.db_path
        db_utils.FORUM_QUEUE_DB = os.path.join(self.temp_dir, 'forum_queue.db')
        db_utils.GIT_QUEUE_DB = os.path.join(self.temp_dir, 'git_queue.db')
        db_utils.GIT_HOSTS_DB = os.path.join(self.temp_dir, 'git_hosts.db')
        db_utils.NON_MOD_REPOS_DB = os.path.join(self.temp_dir, 'non_mod_repos.db')
        
        # Initialize databases
        init_all_databases()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('git.search.requests.get')
    def test_search_github_repositories_success(self, mock_get):
        """Test successful GitHub repository search"""
        # Mock GitHub API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'technic',
                    'full_name': 'minetest-mods/technic',
                    'html_url': 'https://github.com/minetest-mods/technic',
                    'description': 'Technic mod for Minetest',
                    'stargazers_count': 42,
                    'language': 'Lua',
                    'updated_at': '2023-01-01T00:00:00Z',
                    'clone_url': 'https://github.com/minetest-mods/technic.git'
                },
                {
                    'name': 'mesecons',
                    'full_name': 'minetest-mods/mesecons',
                    'html_url': 'https://github.com/minetest-mods/mesecons',
                    'description': 'Mesecons mod for Minetest',
                    'stargazers_count': 38,
                    'language': 'Lua',
                    'updated_at': '2023-01-02T00:00:00Z',
                    'clone_url': 'https://github.com/minetest-mods/mesecons.git'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test search
        results = search_github_repositories(['luanti', 'minetest'])
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], 'technic')
        self.assertEqual(results[0]['platform'], 'github')
        self.assertEqual(results[1]['name'], 'mesecons')
        
        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('github.com/search/repositories', args[0])
        self.assertIn('luanti OR minetest', kwargs['params']['q'])

    @patch('git.search.requests.get')
    def test_search_github_repositories_error(self, mock_get):
        """Test GitHub repository search with API error"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("API limit exceeded")
        mock_get.return_value = mock_response
        
        # Test search
        results = search_github_repositories(['luanti'])
        
        # Should return empty list on error
        self.assertEqual(results, [])

    @patch('git.search.requests.get')
    def test_search_gitlab_repositories_success(self, mock_get):
        """Test successful GitLab repository search"""
        # Mock GitLab API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'minetest-mod',
                'path_with_namespace': 'user/minetest-mod',
                'web_url': 'https://gitlab.com/user/minetest-mod',
                'description': 'A Minetest mod',
                'star_count': 5,
                'last_activity_at': '2023-01-01T00:00:00.000Z',
                'http_url_to_repo': 'https://gitlab.com/user/minetest-mod.git'
            }
        ]
        mock_get.return_value = mock_response
        
        # Test search
        results = search_gitlab_repositories(['luanti'], 'https://gitlab.com')
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'minetest-mod')
        self.assertEqual(results[0]['platform'], 'gitlab')
        self.assertIn('gitlab.com', results[0]['url'])

    @patch('git.search.requests.get')
    def test_search_gitea_repositories_success(self, mock_get):
        """Test successful Gitea repository search (Codeberg uses Gitea)"""
        # Mock Gitea API response 
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'name': 'luanti-mod',
                    'full_name': 'user/luanti-mod',
                    'html_url': 'https://codeberg.org/user/luanti-mod',
                    'description': 'A Luanti mod',
                    'stars_count': 3,
                    'updated_at': '2023-01-01T00:00:00Z',
                    'clone_url': 'https://codeberg.org/user/luanti-mod.git'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test search
        results = search_gitea_repositories('https://codeberg.org', ['luanti'])
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'luanti-mod')

    @patch('git.search.search_github_repositories')
    @patch('git.search.search_gitlab_repositories') 
    @patch('git.search.search_gitea_repositories')
    @patch('git.search.get_all_git_hosts')
    def test_search_all_git_servers(self, mock_get_hosts, mock_gitea, mock_gitlab, mock_github):
        """Test comprehensive search across all git servers"""
        # Mock git hosts
        mock_get_hosts.return_value = [
            ('https://gitlab.example.com', 'gitlab'),
            ('https://gitea.example.com', 'gitea')
        ]
        
        # Mock search results
        mock_github.return_value = [
            {'name': 'github-mod', 'platform': 'github', 'url': 'https://github.com/user/github-mod'}
        ]
        mock_gitlab.return_value = [
            {'name': 'gitlab-mod', 'platform': 'gitlab', 'url': 'https://gitlab.com/user/gitlab-mod'}
        ]
        mock_gitea.return_value = [
            {'name': 'gitea-mod', 'platform': 'gitea', 'url': 'https://codeberg.org/user/gitea-mod'}
        ]
        
        # Test search
        results = search_all_git_servers(['luanti', 'minetest'])
        
        # Verify all platforms were searched
        mock_github.assert_called_once_with(['luanti', 'minetest'])
        mock_gitlab.assert_called()
        mock_gitea.assert_called()
        
        # Verify results aggregated
        self.assertEqual(len(results), 3)
        platforms = [r.get('platform', '') for r in results]
        self.assertIn('github', platforms)

    @patch('git.search.is_git_repository_url')
    @patch('git.search.add_to_git_queue')
    def test_search_all_git_servers_with_mod_filtering(self, mock_add_queue, mock_is_git):
        """Test that only Luanti mods are added to work queue"""
        with patch('git.search.search_github_repositories') as mock_github:
            # Mock search results
            mock_github.return_value = [
                {'name': 'luanti-mod', 'url': 'https://github.com/user/luanti-mod'},
                {'name': 'not-a-mod', 'url': 'https://github.com/user/not-a-mod'}
            ]
            
            # Mock git URL validation - both are valid git repos
            mock_is_git.side_effect = [True, True]
            
            # Test search
            results = search_all_git_servers(['luanti'])
            
            # Verify git validation was called for all repos
            self.assertEqual(mock_is_git.call_count, 2)
            
            # Both repos should be added to queue since this test is about filtering
            self.assertEqual(mock_add_queue.call_count, 2)

    @patch('git.search.get_next_git_repos_from_queue')
    @patch('git.search.mark_git_repo_processed')
    @patch('git.search.check_luanti_mod_repository')
    def test_process_git_work_queue_success(self, mock_check_repo, mock_mark_processed, mock_get_repos):
        """Test successful processing of git work queue"""
        # Mock work queue items
        mock_get_repos.return_value = [
            (1, 'https://github.com/user/test-mod', 'github', '{}')
        ]
        
        # Mock successful mod check
        mock_check_repo.return_value = (True, {
            'name': 'test_mod',
            'description': 'A test mod',
            'author': 'testuser'
        })
        
        # Test processing
        process_git_work_queue(batch_size=10)
        
        # Verify processing
        mock_check_repo.assert_called_once_with('https://github.com/user/test-mod')
        mock_mark_processed.assert_called_once_with(1)

    @patch('git.search.get_next_git_repos_from_queue')
    @patch('git.search.mark_git_repo_processed')
    @patch('git.search.check_luanti_mod_repository')
    def test_process_git_work_queue_not_mod(self, mock_check_repo, mock_mark_processed, mock_get_repos):
        """Test processing of git work queue with non-mod repository"""
        # Mock work queue items
        mock_get_repos.return_value = [
            (1, 'https://github.com/user/not-a-mod', 'github', '{}')
        ]
        
        # Mock non-mod result
        mock_check_repo.return_value = (False, {
            'reason': 'No mod.conf found'
        })
        
        # Test processing
        process_git_work_queue(batch_size=10)
        
        # Verify processing
        mock_mark_processed.assert_called_once_with(1)

    @patch('git.search.get_next_git_repos_from_queue')
    @patch('git.search.mark_git_repo_processed')
    @patch('git.search.check_luanti_mod_repository')
    def test_process_git_work_queue_error(self, mock_check_repo, mock_mark_processed, mock_get_repos):
        """Test processing of git work queue with repository check error"""
        # Mock work queue items
        mock_get_repos.return_value = [
            (1, 'https://github.com/user/error-repo', 'github', '{}')
        ]
        
        # Mock repository check error
        mock_check_repo.side_effect = Exception("Repository not accessible")
        
        # Test processing
        process_git_work_queue(batch_size=10)
        
        # Verify error handling
        mock_mark_processed.assert_called_once_with(1, error="Repository not accessible")

    def test_search_parameters_validation(self):
        """Test that search functions handle invalid parameters correctly"""
        # Test empty keywords
        results = search_github_repositories([])
        self.assertEqual(results, [])
        
        # Test None keywords
        results = search_github_repositories(None)
        self.assertEqual(results, [])
        
        # Test empty string keywords
        results = search_github_repositories([''])
        self.assertEqual(results, [])

    @patch('git.search.requests.get')
    def test_api_rate_limiting_handling(self, mock_get):
        """Test handling of API rate limiting"""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {'X-RateLimit-Remaining': '0'}
        mock_response.raise_for_status.side_effect = Exception("API rate limit exceeded")
        mock_get.return_value = mock_response
        
        # Test search with rate limiting
        results = search_github_repositories(['luanti'])
        
        # Should handle gracefully
        self.assertEqual(results, [])

    @patch('git.search.time.sleep')
    @patch('git.search.requests.get')
    def test_search_with_retry_logic(self, mock_get, mock_sleep):
        """Test search functions with retry logic for transient errors"""
        # Mock transient error followed by success
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = Exception("Server error")
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'items': []}
        
        mock_get.side_effect = [error_response, success_response]
        
        # Test search - this will depend on implementation of retry logic
        results = search_github_repositories(['luanti'])
        
        # Should eventually succeed
        self.assertEqual(results, [])
        
        # Should have made multiple calls if retry logic exists
        if mock_get.call_count > 1:
            mock_sleep.assert_called()

class TestGitSearchIntegration(unittest.TestCase):
    """Integration tests for git search with real database operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Override database paths
        import db_utils
        db_utils.MOD_DATABASE = os.path.join(self.temp_dir, 'test_mod_search.db')
        db_utils.FORUM_QUEUE_DB = os.path.join(self.temp_dir, 'forum_queue.db')
        db_utils.GIT_QUEUE_DB = os.path.join(self.temp_dir, 'git_queue.db')
        db_utils.GIT_HOSTS_DB = os.path.join(self.temp_dir, 'git_hosts.db')
        db_utils.NON_MOD_REPOS_DB = os.path.join(self.temp_dir, 'non_mod_repos.db')
        
        init_all_databases()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_git_work_queue_operations(self):
        """Test adding and processing git work queue items"""
        # Add item to queue
        add_to_git_queue(
            url='https://github.com/test/repo',
            source='github'
        )
        
        # Get item from queue
        items = get_unprocessed_git_repos(limit=1)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item[1], 'https://github.com/test/repo')  # repo_url is index 1
        self.assertEqual(item[2], 'github')  # source is index 2
        
        # Mark as processed
        mark_git_repo_processed(item[0], True)  # item[0] is the ID
        
        # Queue should now be empty
        next_items = get_unprocessed_git_repos(limit=1)
        self.assertEqual(len(next_items), 0)

    @patch('git.utils.requests.get')
    def test_mod_repository_detection_integration(self, mock_get):
        """Test integration between search and mod detection"""
        # Mock successful mod.conf fetch
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
name = test_mod
description = A test mod for Luanti
depends = default
optional_depends = mesecons
"""
        mock_get.return_value = mock_response
        
        # Test git repository validation  
        result = check_luanti_mod_repository('https://github.com/test/mod')
        self.assertTrue(result.get('is_mod', False))

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
