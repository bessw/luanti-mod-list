import requests
import time
import json
from urllib.parse import quote
import sys
import os

# Add parent directory to path to import db_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_utils import (
    add_to_git_queue, is_git_repo_in_queue, 
    get_all_git_hosts, add_git_host
)

# Rate limiting delays (seconds)
GITHUB_DELAY = 1.2  # GitHub allows 60 requests per hour for unauthenticated requests
GITLAB_DELAY = 0.5  # GitLab.com allows 2000 requests per minute for unauthenticated requests
GITEA_DELAY = 0.3   # Most Gitea instances are more lenient

def search_github_repositories(keywords, max_results=100):
    """Search GitHub for repositories containing the keywords"""
    all_repos = []
    
    for keyword in keywords:
        print(f"Searching GitHub for: {keyword}")
        repos = _search_github_api(keyword, max_results // len(keywords))
        all_repos.extend(repos)
        time.sleep(GITHUB_DELAY)
    
    # Remove duplicates based on URL
    unique_repos = {}
    for repo in all_repos:
        unique_repos[repo['url']] = repo
    
    return list(unique_repos.values())

def search_gitlab_repositories(host_url, keywords, max_results=100):
    """Search GitLab for repositories containing the keywords"""
    all_repos = []
    
    for keyword in keywords:
        print(f"Searching {host_url} for: {keyword}")
        repos = _search_gitlab_api(host_url, keyword, max_results // len(keywords))
        all_repos.extend(repos)
        time.sleep(GITLAB_DELAY)
    
    # Remove duplicates based on URL
    unique_repos = {}
    for repo in all_repos:
        unique_repos[repo['url']] = repo
    
    return list(unique_repos.values())

def search_gitea_repositories(host_url, keywords, max_results=100):
    """Search Gitea for repositories containing the keywords"""
    all_repos = []
    
    for keyword in keywords:
        print(f"Searching {host_url} for: {keyword}")
        repos = _search_gitea_api(host_url, keyword, max_results // len(keywords))
        all_repos.extend(repos)
        time.sleep(GITEA_DELAY)
    
    # Remove duplicates based on URL
    unique_repos = {}
    for repo in all_repos:
        unique_repos[repo['url']] = repo
    
    return list(unique_repos.values())

def search_all_git_servers(keywords=None, max_results_per_host=50):
    """Search all known git servers for Luanti/Minetest repositories"""
    if keywords is None:
        keywords = ['luanti', 'minetest']
    
    all_repositories = []
    
    # Search GitHub
    print("=== Searching GitHub ===")
    github_repos = search_github_repositories(keywords, max_results_per_host)
    all_repositories.extend(github_repos)
    
    # Add repositories to git work queue
    added_count = 0
    for repo in github_repos:
        if not is_git_repo_in_queue(repo['url']):
            add_to_git_queue(
                url=repo['url'],
                source='github_search',
                priority=1,
                metadata=json.dumps({
                    'name': repo.get('name', ''),
                    'description': repo.get('description', ''),
                    'stars': repo.get('stars', 0),
                    'language': repo.get('language', ''),
                    'keywords': keywords
                })
            )
            added_count += 1
    print(f"Added {added_count} GitHub repositories to work queue")
    
    # Search all known GitLab instances
    gitlab_hosts = get_all_git_hosts('gitlab') + get_all_git_hosts('gitlab-selfhosted')
    if not gitlab_hosts:
        # Add GitLab.com if no hosts are known
        add_git_host('https://gitlab.com', 'gitlab')
        gitlab_hosts = [('https://gitlab.com', 'gitlab')]
    
    for host_url, host_type in gitlab_hosts:
        print(f"=== Searching GitLab: {host_url} ===")
        try:
            gitlab_repos = search_gitlab_repositories(host_url, keywords, max_results_per_host)
            all_repositories.extend(gitlab_repos)
            
            # Add repositories to git work queue
            added_count = 0
            for repo in gitlab_repos:
                if not is_git_repo_in_queue(repo['url']):
                    add_to_git_queue(
                        url=repo['url'],
                        source='gitlab_search',
                        priority=1,
                        metadata=json.dumps({
                            'name': repo.get('name', ''),
                            'description': repo.get('description', ''),
                            'stars': repo.get('stars', 0),
                            'host': host_url,
                            'keywords': keywords
                        })
                    )
                    added_count += 1
            print(f"Added {added_count} GitLab repositories to work queue")
            
        except Exception as e:
            print(f"Error searching {host_url}: {e}")
    
    # Search all known Gitea instances
    gitea_hosts = get_all_git_hosts('gitea')
    for host_url, host_type in gitea_hosts:
        print(f"=== Searching Gitea: {host_url} ===")
        try:
            gitea_repos = search_gitea_repositories(host_url, keywords, max_results_per_host)
            all_repositories.extend(gitea_repos)
            
            # Add repositories to git work queue
            added_count = 0
            for repo in gitea_repos:
                if not is_git_repo_in_queue(repo['url']):
                    add_to_git_queue(
                        url=repo['url'],
                        source='gitea_search',
                        priority=1,
                        metadata=json.dumps({
                            'name': repo.get('name', ''),
                            'description': repo.get('description', ''),
                            'stars': repo.get('stars', 0),
                            'host': host_url,
                            'keywords': keywords
                        })
                    )
                    added_count += 1
            print(f"Added {added_count} Gitea repositories to work queue")
            
        except Exception as e:
            print(f"Error searching {host_url}: {e}")
    
    return all_repositories

def _search_github_api(query, max_results=30):
    """Search GitHub API for repositories"""
    repositories = []
    
    try:
        # GitHub Search API
        url = f"https://api.github.com/search/repositories"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(max_results, 100)  # GitHub API limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        for item in data.get('items', []):
            repositories.append({
                'url': item.get('html_url', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'stars': item.get('stargazers_count', 0),
                'forks': item.get('forks_count', 0),
                'language': item.get('language', ''),
                'owner': item.get('owner', {}).get('login', ''),
                'topics': item.get('topics', [])
            })
    
    except requests.exceptions.RequestException as e:
        print(f"Error searching GitHub: {e}")
    except Exception as e:
        print(f"Unexpected error searching GitHub: {e}")
    
    return repositories[:max_results]

def _search_gitlab_api(host_url, query, max_results=30):
    """Search GitLab API for repositories"""
    repositories = []
    
    try:
        # GitLab Search API
        api_url = f"{host_url.rstrip('/')}/api/v4/projects"
        params = {
            'search': query,
            'order_by': 'star_count',
            'sort': 'desc',
            'per_page': min(max_results, 100),  # GitLab API limit
            'simple': 'true'
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        for item in data:
            repositories.append({
                'url': item.get('web_url', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'stars': item.get('star_count', 0),
                'forks': item.get('forks_count', 0),
                'owner': item.get('namespace', {}).get('name', ''),
                'topics': item.get('topics', [])
            })
    
    except requests.exceptions.RequestException as e:
        print(f"Error searching GitLab at {host_url}: {e}")
    except Exception as e:
        print(f"Unexpected error searching GitLab at {host_url}: {e}")
    
    return repositories[:max_results]

def _search_gitea_api(host_url, query, max_results=30):
    """Search Gitea API for repositories"""
    repositories = []
    
    try:
        # Gitea Search API
        api_url = f"{host_url.rstrip('/')}/api/v1/repos/search"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'limit': min(max_results, 50)  # Gitea API typical limit
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        for item in data.get('data', []):
            repositories.append({
                'url': item.get('html_url', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'stars': item.get('stars_count', 0),
                'forks': item.get('forks_count', 0),
                'language': item.get('language', ''),
                'owner': item.get('owner', {}).get('login', ''),
                'topics': item.get('topics', [])
            })
    
    except requests.exceptions.RequestException as e:
        print(f"Error searching Gitea at {host_url}: {e}")
    except Exception as e:
        print(f"Unexpected error searching Gitea at {host_url}: {e}")
    
    return repositories[:max_results]

def process_git_work_queue(batch_size=10):
    """Process repositories from git work queue and check if they are Luanti mods"""
    from .utils import check_luanti_mod_repository  # Import locally to avoid circular imports
    
    # Get repositories from work queue
    repos_to_process = get_next_git_repos_from_queue(batch_size)
    
    if not repos_to_process:
        print("No repositories in git work queue to process")
        return
    
    print(f"Processing {len(repos_to_process)} repositories from git work queue...")
    
    processed_count = 0
    mods_found = 0
    
    for repo_id, repo_url, source, metadata_str in repos_to_process:
        print(f"Checking repository: {repo_url}")
        
        try:
            # Check if it's a Luanti mod
            is_mod, mod_metadata = check_luanti_mod_repository(repo_url)
            
            if is_mod:
                # Add to mod list database
                from db_utils import add_mod_to_db
                
                # Parse existing metadata
                existing_metadata = {}
                if metadata_str:
                    try:
                        existing_metadata = json.loads(metadata_str)
                    except:
                        pass
                
                # Combine metadata
                combined_metadata = {**existing_metadata, **mod_metadata}
                combined_metadata['source'] = 'git_repository'
                combined_metadata['git_url'] = repo_url
                
                # Add to mod database
                add_mod_to_db(
                    name=mod_metadata.get('name', combined_metadata.get('name', 'Unknown')),
                    mod_type=mod_metadata.get('type', 'mod'),
                    author=mod_metadata.get('author', combined_metadata.get('owner', 'Unknown')),
                    description=mod_metadata.get('description', combined_metadata.get('description', '')),
                    source='git_repository',
                    url=repo_url,
                    metadata=json.dumps(combined_metadata)
                )
                
                print(f"  ✓ Found {mod_metadata.get('type', 'mod')}: {mod_metadata.get('name', 'Unknown')}")
                mods_found += 1
            else:
                print(f"  ✗ Not a Luanti mod")
            
            # Remove from work queue (mark as processed)
            mark_git_repo_processed(repo_id)
            processed_count += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {repo_url}: {e}")
            # Mark as processed with error
            mark_git_repo_processed(repo_id, error=str(e))
    
    print(f"Processed {processed_count} repositories, found {mods_found} mods")

def get_next_git_repos_from_queue(batch_size=10):
    """Get next batch of repositories from git work queue"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('git_queue.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, source, metadata
            FROM git_work_queue 
            WHERE processed = 0 
            ORDER BY priority DESC, added_date ASC 
            LIMIT ?
        ''', (batch_size,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"Error getting repositories from git work queue: {e}")
        return []

def mark_git_repo_processed(repo_id, error=None):
    """Mark a repository as processed in the git work queue"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('git_queue.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE git_work_queue 
            SET processed = 1, processed_date = datetime('now'), error = ?
            WHERE id = ?
        ''', (error, repo_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error marking repository {repo_id} as processed: {e}")

if __name__ == "__main__":
    # Example usage: search all git servers and process work queue
    print("Searching all git servers for Luanti/Minetest repositories...")
    repositories = search_all_git_servers()
    print(f"Found {len(repositories)} repositories across all git servers")
    
    print("\nProcessing git work queue...")
    process_git_work_queue()
