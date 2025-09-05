import requests
import re
from urllib.parse import urljoin, urlparse
import sys
import os

# Add parent directory to path to import db_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_utils import add_mod_to_db

# ContentDB API base URL
CONTENTDB_API_BASE = "https://content.minetest.net/api"

def fetch_all_packages():
    """Fetch all packages from ContentDB"""
    packages = []
    page = 1
    
    while True:
        print(f"Fetching ContentDB page {page}...")
        
        try:
            response = requests.get(f"{CONTENTDB_API_BASE}/packages/", 
                                  params={"page": page, "per_page": 50})
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                break
                
            packages.extend(data)
            
            # If we got less than 50 items, we're on the last page
            if len(data) < 50:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching ContentDB packages: {e}")
            break
    
    return packages

def get_package_details(package_id):
    """Get detailed information about a specific package"""
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/{package_id}/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching package details for {package_id}: {e}")
        return None

def search_packages(query, package_type=None):
    """Search ContentDB packages"""
    params = {"q": query}
    if package_type:
        params["type"] = package_type
        
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching ContentDB: {e}")
        return []

def sync_contentdb_to_database():
    """Sync all ContentDB packages to local database"""
    print("Starting ContentDB sync...")
    
    packages = fetch_all_packages()
    print(f"Found {len(packages)} packages on ContentDB")
    
    added_count = 0
    updated_count = 0
    
    for package in packages:
        try:
            # Get detailed package info
            package_details = get_package_details(f"{package['author']}/{package['name']}")
            
            if not package_details:
                continue
            
            # Determine package type
            package_type = package_details.get('type', 'mod')
            
            # Extract repository URL if available
            repo_url = None
            if 'repo' in package_details and package_details['repo']:
                repo_url = package_details['repo']
            elif 'website' in package_details and package_details['website']:
                # Sometimes the website is the repo
                website = package_details['website']
                if any(host in website.lower() for host in ['github.com', 'gitlab.com', 'codeberg.org']):
                    repo_url = website
            
            # Build metadata
            metadata = {
                'contentdb_id': package_details.get('name', ''),
                'contentdb_author': package_details.get('author', ''),
                'contentdb_url': f"https://content.minetest.net/packages/{package_details.get('author', '')}/{package_details.get('name', '')}",
                'short_description': package_details.get('short_description', ''),
                'tags': package_details.get('tags', []),
                'license': package_details.get('license', ''),
                'media_license': package_details.get('media_license', ''),
                'created_at': package_details.get('created_at', ''),
                'downloads': package_details.get('downloads', 0),
                'score': package_details.get('score', 0),
                'reviews': package_details.get('reviews', 0),
                'min_minetest_version': package_details.get('min_minetest_version', ''),
                'max_minetest_version': package_details.get('max_minetest_version', ''),
            }
            
            if repo_url:
                metadata['git_url'] = repo_url
            
            # Add to database
            result = add_mod_to_db(
                name=package_details.get('name', ''),
                mod_type=package_type,
                author=package_details.get('author', ''),
                description=package_details.get('short_description', ''),
                source='contentdb',
                url=f"https://content.minetest.net/packages/{package_details.get('author', '')}/{package_details.get('name', '')}",
                metadata=metadata
            )
            
            if result:
                if result == 'added':
                    added_count += 1
                else:
                    updated_count += 1
            
            if (added_count + updated_count) % 50 == 0:
                print(f"Processed {added_count + updated_count} packages...")
        
        except Exception as e:
            print(f"Error processing package {package.get('name', 'unknown')}: {e}")
            continue
    
    print(f"ContentDB sync complete: {added_count} added, {updated_count} updated")
    return added_count, updated_count

def get_package_dependencies(package_id):
    """Get dependencies for a package"""
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/{package_id}/dependencies/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dependencies for {package_id}: {e}")
        return []

def search_by_author(author):
    """Get all packages by a specific author"""
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/", 
                              params={"author": author})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching packages by author {author}: {e}")
        return []

def get_popular_packages(limit=50):
    """Get most popular packages by download count"""
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/", 
                              params={"sort": "downloads", "order": "desc", "per_page": limit})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching popular packages: {e}")
        return []

def get_recently_updated_packages(limit=50):
    """Get recently updated packages"""
    try:
        response = requests.get(f"{CONTENTDB_API_BASE}/packages/", 
                              params={"sort": "last_release", "order": "desc", "per_page": limit})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recently updated packages: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    print("Testing ContentDB API...")
    
    # Search for a specific mod
    results = search_packages("technic", "mod")
    print(f"Found {len(results)} mods matching 'technic'")
    
    # Get popular packages
    popular = get_popular_packages(10)
    print(f"\nTop 10 popular packages:")
    for pkg in popular[:10]:
        print(f"  {pkg.get('title', pkg.get('name'))}: {pkg.get('downloads', 0)} downloads")
    
    # Sync all packages (uncomment to run full sync)
    # sync_contentdb_to_database()
