"""
Test cases for ContentDB API functions
"""
import unittest
from contentdb.api import search_packages
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
        results = search_packages("mesecons", package_type="mod")
        
        # Assert we got at least one result
        self.assertGreater(len(results), 0, "Should return at least one result")
        
        # Check the structure of the first result
        result = results[0]
        
        # Check required fields are present
        self.assertIn("title", result)
        self.assertIn("author", result)
        self.assertIn("type", result)
        
        print(f"Test result: {result['title']} by {result['author']}")
        print(f"ContentDB URL: https://content.luanti.org/packages/{result['author']}/{result['name']}/")
        print(f"Forum URL: {result.get('forum_url', 'N/A')}")
        print(f"Repo URL: {result.get('repo_url', 'N/A')}")

if __name__ == '__main__':
    unittest.main()
