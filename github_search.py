import requests
from db_utils import get_git_hosts, add_git_repo_to_queue, git_repo_in_queue
from urllib.parse import urljoin

def search_github_mods(query):
    """Search GitHub repositories for Luanti mods"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{query}"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("items", [])

def search_github_by_topic(topic):
    """Search GitHub repositories by topic"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"topic:{topic}"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("items", [])

def search_all_git_servers(query_terms=None, topics=None):
    """
    Search all known git servers for Luanti-related repositories
    
    Args:
        query_terms: List of keywords to search for (default: ["luanti", "minetest"])
        topics: List of topics to search for (default: ["luanti-mod", "minetest-mod", "luanti", "minetest"])
    
    Returns:
        Dictionary with results from each server
    """
    if query_terms is None:
        query_terms = ["luanti", "minetest"]
    if topics is None:
        topics = ["luanti-mod", "minetest-mod", "luanti", "minetest"]
    
    results = {
        'github': [],
        'gitlab': [],
        'codeberg': [],
        'gitea': [],
        'other': []
    }
    
    # Search GitHub
    print("Searching GitHub...")
    for query in query_terms:
        github_results = search_github_mods(query)
        results['github'].extend(github_results)
        _add_repos_to_queue(github_results, 'github-search')
    
    for topic in topics:
        topic_results = search_github_by_topic(topic)
        results['github'].extend(topic_results)
        _add_repos_to_queue(topic_results, 'github-topic')
    
    # Search GitLab.com
    print("Searching GitLab.com...")
    gitlab_results = []
    for query in query_terms:
        repos = search_gitlab_repositories("https://gitlab.com", query)
        gitlab_results.extend(repos)
    results['gitlab'] = gitlab_results
    _add_repos_to_queue(gitlab_results, 'gitlab-search')
    
    # Search Codeberg
    print("Searching Codeberg...")
    codeberg_results = []
    for query in query_terms:
        repos = search_gitea_repositories("https://codeberg.org", query)
        codeberg_results.extend(repos)
    results['codeberg'] = codeberg_results
    _add_repos_to_queue(codeberg_results, 'codeberg-search')
    
    # Search known self-hosted instances
    git_hosts = get_git_hosts()
    for host_url, host_type in git_hosts:
        if host_type in ['gitlab-selfhosted']:
            print(f"Searching GitLab instance: {host_url}")
            host_results = []
            for query in query_terms:
                repos = search_gitlab_repositories(host_url, query)
                host_results.extend(repos)
            results['gitlab'].extend(host_results)
            _add_repos_to_queue(host_results, f'gitlab-{host_url}')
        
        elif host_type in ['gitea']:
            print(f"Searching Gitea instance: {host_url}")
            host_results = []
            for query in query_terms:
                repos = search_gitea_repositories(host_url, query)
                host_results.extend(repos)
            results['gitea'].extend(host_results)
            _add_repos_to_queue(host_results, f'gitea-{host_url}')
    
    return results

def search_gitlab_repositories(gitlab_url, query):
    """Search GitLab repositories using the GitLab API"""
    try:
        api_url = f"{gitlab_url}/api/v4/projects"
        params = {
            "search": query,
            "simple": True,
            "per_page": 50
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        if response.status_code == 200:
            projects = response.json()
            return [_convert_gitlab_to_standard(project, gitlab_url) for project in projects]
    except requests.RequestException as e:
        print(f"Error searching GitLab at {gitlab_url}: {e}")
    
    return []

def search_gitea_repositories(gitea_url, query):
    """Search Gitea repositories using the Gitea API"""
    try:
        api_url = f"{gitea_url}/api/v1/repos/search"
        params = {
            "q": query,
            "limit": 50
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            repos = data.get('data', [])
            return [_convert_gitea_to_standard(repo, gitea_url) for repo in repos]
    except requests.RequestException as e:
        print(f"Error searching Gitea at {gitea_url}: {e}")
    
    return []

def _convert_gitlab_to_standard(project, gitlab_url):
    """Convert GitLab project format to standard repository format"""
    return {
        'html_url': project.get('web_url', ''),
        'name': project.get('name', ''),
        'full_name': project.get('path_with_namespace', ''),
        'description': project.get('description', ''),
        'owner': {'login': project.get('namespace', {}).get('name', '')},
        'clone_url': project.get('http_url_to_repo', ''),
        'stargazers_count': project.get('star_count', 0),
        'forks_count': project.get('forks_count', 0),
        'topics': project.get('topics', []),
        'language': None,  # GitLab API might not provide this in simple mode
        'created_at': project.get('created_at', ''),
        'updated_at': project.get('last_activity_at', ''),
    }

def _convert_gitea_to_standard(repo, gitea_url):
    """Convert Gitea repository format to standard repository format"""
    return {
        'html_url': repo.get('html_url', ''),
        'name': repo.get('name', ''),
        'full_name': repo.get('full_name', ''),
        'description': repo.get('description', ''),
        'owner': {'login': repo.get('owner', {}).get('login', '')},
        'clone_url': repo.get('clone_url', ''),
        'stargazers_count': repo.get('stars_count', 0),
        'forks_count': repo.get('forks_count', 0),
        'topics': [],  # Gitea might not provide topics in search results
        'language': repo.get('language', ''),
        'created_at': repo.get('created_at', ''),
        'updated_at': repo.get('updated_at', ''),
    }

def _add_repos_to_queue(repos, source):
    """Add repository URLs to the git work queue if not already present"""
    added_count = 0
    for repo in repos:
        repo_url = repo.get('html_url', '')
        if repo_url and not git_repo_in_queue(repo_url):
            if add_git_repo_to_queue(repo_url, source):
                added_count += 1
    
    if added_count > 0:
        print(f"  Added {added_count} new repositories to git work queue from {source}")
    
    return added_count
