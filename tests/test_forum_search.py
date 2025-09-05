"""
Unit tests for forum search functionality
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import sqlite3

# Import our modules
from forum_search import (fetch_forum_thread_list, process_forum_thread, 
                         process_forum_work_queue)
from db_utils import (init_db, add_forum_thread_to_queue, get_unprocessed_forum_threads,
                      mark_forum_thread_processed, FORUM_QUEUE_DB)

class TestForumSearch(unittest.TestCase):
    
    def setUp(self):
        """Set up test databases in temporary files"""
        # Create temporary database files
        self.temp_dir = tempfile.mkdtemp()
        self.original_forum_db = FORUM_QUEUE_DB
        
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
        
        # Restore original database paths
        import db_utils
        db_utils.FORUM_QUEUE_DB = self.original_forum_db
    
    @patch('forum_search.requests.get')
    def test_fetch_forum_thread_list(self, mock_get):
        """Test fetching and parsing forum thread list"""
        # Mock HTML response with forum threads
        mock_html = '''
        <html>
        <body>
            <a class="topictitle" href="./viewtopic.php?t=1">[Mod] Test Mod</a>
            <a class="topictitle" href="./viewtopic.php?t=2">[Game] Test Game</a>
            <a class="topictitle" href="./viewtopic.php?t=3">[Modpack] Test Modpack</a>
            <a class="topictitle" href="./viewtopic.php?t=4">Regular Thread</a>
        </body>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # Test the function
        forum_url = "https://forum.luanti.org/viewforum.php?f=11"
        added_threads = fetch_forum_thread_list(forum_url)
        
        # Verify request was made
        mock_get.assert_called_once_with(forum_url)
        
        # Should have added 3 threads (mod, game, modpack) but not the regular thread
        self.assertEqual(len(added_threads), 3)
        
        # Verify threads were added to queue
        threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(threads), 3)
        
        # Check thread types are correct
        thread_titles = [thread[2] for thread in threads]  # title is at index 2
        thread_types = [thread[3] for thread in threads]   # type is at index 3
        
        self.assertIn("[Mod] Test Mod", thread_titles)
        self.assertIn("[Game] Test Game", thread_titles)
        self.assertIn("[Modpack] Test Modpack", thread_titles)
        
        self.assertIn("mod", thread_types)
        self.assertIn("game", thread_types)
        self.assertIn("modpack", thread_types)
    
    @patch('forum_search.check_luanti_mod_repository')
    @patch('forum_search.is_git_repository_url')
    @patch('forum_search.requests.get')
    def test_process_forum_thread(self, mock_get, mock_is_git, mock_check_mod):
        """Test processing a single forum thread"""
        # Add a thread to the queue
        thread_url = "https://forum.luanti.org/viewtopic.php?t=123"
        add_forum_thread_to_queue(thread_url, "Test Mod Thread", "mod")
        
        # Mock HTML response with git repository links
        mock_html = '''
        <html>
        <body>
            <div class="post">
                <div class="content">
                    <p>Check out my mod at <a href="https://github.com/user/testmod">GitHub</a></p>
                    <p>Also available at <a href="https://gitlab.com/user/testmod">GitLab</a></p>
                    <p>Regular link: <a href="https://example.com">Example</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # Mock git repository detection
        def mock_git_check(url):
            if 'github.com' in url or 'gitlab.com' in url:
                return True, 'github' if 'github.com' in url else 'gitlab'
            return False, None
        mock_is_git.side_effect = mock_git_check
        
        # Mock mod check - return True for GitHub repo
        def mock_mod_check(url):
            if 'github.com' in url:
                return True, {
                    'name': 'testmod',
                    'description': 'A test mod',
                    'author': 'testuser',
                    'type': 'mod'
                }
            return False, None
        mock_check_mod.side_effect = mock_mod_check
        
        # Get thread from queue
        threads = get_unprocessed_forum_threads(1)
        self.assertEqual(len(threads), 1)
        thread_id, forum_url, title, thread_type = threads[0]
        
        # Process the thread
        result = process_forum_thread(thread_id, forum_url, title, thread_type)
        
        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["git_repos_found"], 2)  # GitHub and GitLab
        self.assertEqual(result["luanti_mods_found"], 1)  # Only GitHub is a mod
        
        # Verify thread was marked as processed
        remaining_threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(remaining_threads), 0)
    
    def test_work_queue_management(self):
        """Test work queue operations"""
        # Test adding threads to queue
        thread1 = "https://forum.luanti.org/viewtopic.php?t=1"
        thread2 = "https://forum.luanti.org/viewtopic.php?t=2"
        
        # Add threads
        self.assertTrue(add_forum_thread_to_queue(thread1, "Test Mod 1", "mod"))
        self.assertTrue(add_forum_thread_to_queue(thread2, "Test Game 1", "game"))
        
        # Try to add duplicate - should return False
        self.assertFalse(add_forum_thread_to_queue(thread1, "Test Mod 1 Duplicate", "mod"))
        
        # Get unprocessed threads
        threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(threads), 2)
        
        # Mark one as processed
        thread_id = threads[0][0]
        mark_forum_thread_processed(thread_id)
        
        # Should now have only one unprocessed thread
        remaining_threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(remaining_threads), 1)
        
        # Process remaining thread
        mark_forum_thread_processed(remaining_threads[0][0])
        
        # Should have no unprocessed threads
        final_threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(final_threads), 0)
    
    @patch('forum_search.process_forum_thread')
    def test_process_forum_work_queue(self, mock_process):
        """Test batch processing of forum work queue"""
        # Add multiple threads to queue
        threads_data = [
            ("https://forum.luanti.org/viewtopic.php?t=1", "Mod 1", "mod"),
            ("https://forum.luanti.org/viewtopic.php?t=2", "Game 1", "game"),
            ("https://forum.luanti.org/viewtopic.php?t=3", "Modpack 1", "modpack"),
        ]
        
        for url, title, thread_type in threads_data:
            add_forum_thread_to_queue(url, title, thread_type)
        
        # Mock successful processing that doesn't mark as processed (process_forum_work_queue handles that)
        def mock_process_thread(thread_id, forum_url, title, thread_type):
            # Don't mark as processed here - process_forum_work_queue should handle it
            # but our mock bypasses that, so we need to mark it ourselves in the test
            mark_forum_thread_processed(thread_id)
            return {
                "status": "success",
                "git_repos_found": 1,
                "luanti_mods_found": 1
            }
        
        mock_process.side_effect = mock_process_thread
        
        # Process work queue with batch size 2
        results = process_forum_work_queue(batch_size=2)
        
        # Should have processed 2 threads
        self.assertEqual(len(results), 2)
        self.assertEqual(mock_process.call_count, 2)
        
        # Should have 1 thread remaining in queue
        remaining_threads = get_unprocessed_forum_threads(10)
        self.assertEqual(len(remaining_threads), 1)

if __name__ == '__main__':
    unittest.main()
