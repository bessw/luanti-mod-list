"""
Test cases for ContentDB API functions
"""
import unittest
from contentdb_api import search_contentdb_mods
from db_utils import init_db, contentdb_url_exists
import sqlite3
import os

class TestContentDBAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        # Use a test database
        self.test_db = "test_mod_search_results.db"
        # Remove existing test db if it exists
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Temporarily override the DB_PATH for testing
        import db_utils
        self.original_db_path = db_utils.DB_PATH
        db_utils.DB_PATH = self.test_db
        
        # Initialize test database
        init_db()
    
    def tearDown(self):
        """Clean up test database"""
        import db_utils
        db_utils.DB_PATH = self.original_db_path
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_search_contentdb_mods_single_result(self):
        """Test fetching a single result from ContentDB"""
        # Search for a specific mod that should exist
        results = search_contentdb_mods("mesecons", page=1, per_page=1)
        
        # Assert we got at least one result
        self.assertGreater(len(results), 0, "Should return at least one result")
        
        # Check the structure of the first result
        result = results[0]
        
        # Check required fields are present
        self.assertIn("contentdb_url", result)
        self.assertIn("title", result)
        self.assertIn("author", result)
        self.assertIn("type", result)
        
        # Check that contentdb_url is not empty
        self.assertNotEqual(result["contentdb_url"], "", "contentdb_url should not be empty")
        
        # Check that the result was saved to database
        self.assertTrue(contentdb_url_exists(result["contentdb_url"]), 
                       "Result should be saved to database")
        
        print(f"Test result: {result['title']} by {result['author']}")
        print(f"ContentDB URL: https://content.luanti.org/packages/{result['author']}/{result['name']}/")
        print(f"ContentDB Download URL: {result['contentdb_url']}")
        print(f"Forum URL: {result.get('forum_url', 'N/A')}")
        print(f"Repo URL: {result.get('repo_url', 'N/A')}")

if __name__ == '__main__':
    unittest.main()
