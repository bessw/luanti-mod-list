import requests
import re
import base64
from urllib.parse import urlparse, urljoin
import sys
import os

# Add parent directory to path to import db_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_utils import add_git_host, is_known_non_mod_repo, add_non_mod_repo

def is_git_repository_url(url):
    """Check if a URL is a git repository and identify the host type"""
    if not url:
        return False, None
    
    # First check known hosting providers
    if _is_known_git_host(url):
        return _is_known_git_host(url)
    
    # Check if it's a potential git repository URL and determine host type
    if _looks_like_git_repo_url(url):
        return _detect_git_host_type(url)
    
    return False, None

def _is_known_git_host(url):
    """Check against known git hosting patterns"""
    known_patterns = [
        # GitHub
        (r'https://github\.com/[\w\-\.]+/[\w\-\.]+/?$', 'github'),
        # GitLab.com
        (r'https://gitlab\.com/[\w\-\.]+/[\w\-\.]+/?$', 'gitlab'),
        # Codeberg
        (r'https://codeberg\.org/[\w\-\.]+/[\w\-\.]+/?$', 'codeberg'),
        # Bitbucket
        (r'https://bitbucket\.org/[\w\-\.]+/[\w\-\.]+/?$', 'bitbucket'),
        # SourceForge
        (r'https://sourceforge\.net/projects/[\w\-\.]+/?$', 'sourceforge'),
        # Git URLs ending with .git
        (r'https?://.*\.git$', 'git'),
    ]
    
    for pattern, host_type in known_patterns:
        if re.match(pattern, url):
            return True, host_type
    
    return False, None

def _looks_like_git_repo_url(url):
    """Check if URL looks like it could be a git repository"""
    # Pattern for potential git repository URLs (host/user/repo)
    git_repo_pattern = r'https://[\w\-\.]+/[\w\-\.]+/[\w\-\.]+/?$'
    return re.match(git_repo_pattern, url) is not None

def _detect_git_host_type(url):
    """Detect the type of git hosting service by checking the server"""
    if not _looks_like_git_repo_url(url):
        return False, None
    
    parsed = urlparse(url)
    host_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Check if it's GitLab by looking for manifest.json
    if _is_gitlab_instance(host_url):
        add_git_host(host_url, 'gitlab-selfhosted')
        return True, 'gitlab-selfhosted'
    
    # Check if it's Gitea by looking for "Powered by Gitea" on main page
    if _is_gitea_instance(host_url):
        add_git_host(host_url, 'gitea')
        return True, 'gitea'
    
    # Default to generic git if we can't determine the type
    add_git_host(host_url, 'git-unknown')
    return True, 'git-unknown'

def _is_gitlab_instance(host_url):
    """Check if a host is a GitLab instance by checking manifest.json"""
    try:
        manifest_url = f"{host_url}/-/manifest.json"
        response = requests.get(manifest_url, timeout=10)
        if response.status_code == 200:
            try:
                manifest = response.json()
                return manifest.get("name") == "GitLab"
            except ValueError:
                return False
    except requests.RequestException:
        pass
    return False

def _is_gitea_instance(host_url):
    """Check if a host is a Gitea instance by looking for 'Powered by Gitea' link"""
    try:
        response = requests.get(host_url, timeout=10)
        if response.status_code == 200:
            # Look for "Powered by Gitea" in the HTML
            return 'Powered by Gitea' in response.text
    except requests.RequestException:
        pass
    return False

def check_luanti_mod_repository(repo_url):
    """
    Check if a git repository contains a Luanti mod by looking for mod.conf
    Returns: (is_mod, metadata) where metadata contains mod info if is_mod is True
    """
    if is_known_non_mod_repo(repo_url):
        return False, None
    
    try:
        # Try to get mod.conf from different possible locations
        possible_paths = [
            'mod.conf',
            'mods/*/mod.conf',  # For modpacks
            'games/*/game.conf',  # For games
        ]
        
        metadata = {}
        is_mod = False
        
        # GitHub API approach
        if 'github.com' in repo_url:
            # Extract owner and repo name from URL
            match = re.match(r'https://github\.com/([\w\-\.]+)/([\w\-\.]+)/?', repo_url)
            if match:
                owner, repo = match.groups()
                
                # Check for mod.conf
                mod_conf_url = f"https://api.github.com/repos/{owner}/{repo}/contents/mod.conf"
                response = requests.get(mod_conf_url)
                
                if response.status_code == 200:
                    # Get mod.conf content
                    content = base64.b64decode(response.json()['content']).decode('utf-8')
                    metadata = _parse_mod_conf(content)
                    is_mod = True
                else:
                    # Check for game.conf (Luanti games)
                    game_conf_url = f"https://api.github.com/repos/{owner}/{repo}/contents/game.conf"
                    response = requests.get(game_conf_url)
                    
                    if response.status_code == 200:
                        content = base64.b64decode(response.json()['content']).decode('utf-8')
                        metadata = _parse_game_conf(content)
                        metadata['type'] = 'game'
                        is_mod = True
                    else:
                        # Check if it's a modpack (has mods/ directory)
                        mods_dir_url = f"https://api.github.com/repos/{owner}/{repo}/contents/mods"
                        response = requests.get(mods_dir_url)
                        
                        if response.status_code == 200:
                            # It's likely a modpack
                            metadata = {
                                'name': repo,
                                'type': 'modpack',
                                'description': f"Modpack from {repo_url}"
                            }
                            is_mod = True
        
        # GitLab API approach (similar pattern)
        elif 'gitlab.com' in repo_url:
            # Extract project path from URL
            match = re.match(r'https://gitlab\.com/([\w\-\.]+/[\w\-\.]+)/?', repo_url)
            if match:
                project_path = match.group(1)
                
                # Check for mod.conf
                mod_conf_url = f"https://gitlab.com/api/v4/projects/{project_path.replace('/', '%2F')}/repository/files/mod.conf/raw?ref=master"
                response = requests.get(mod_conf_url)
                
                if response.status_code == 200:
                    metadata = _parse_mod_conf(response.text)
                    is_mod = True
                else:
                    # Check for game.conf
                    game_conf_url = f"https://gitlab.com/api/v4/projects/{project_path.replace('/', '%2F')}/repository/files/game.conf/raw?ref=master"
                    response = requests.get(game_conf_url)
                    
                    if response.status_code == 200:
                        metadata = _parse_game_conf(response.text)
                        metadata['type'] = 'game'
                        is_mod = True
        
        # Generic approach - try to access mod.conf directly
        else:
            # Try common patterns for accessing raw files
            raw_urls = [
                f"{repo_url.rstrip('/')}/raw/master/mod.conf",
                f"{repo_url.rstrip('/')}/raw/main/mod.conf",
                f"{repo_url.rstrip('/')}/raw/HEAD/mod.conf",
                f"{repo_url.rstrip('/')}/plain/mod.conf",
            ]
            
            for raw_url in raw_urls:
                try:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        metadata = _parse_mod_conf(response.text)
                        is_mod = True
                        break
                except requests.RequestException:
                    continue
        
        if not is_mod:
            # Mark as non-mod repo
            add_non_mod_repo(repo_url, "No mod.conf or game.conf found")
            return False, None
            
        return is_mod, metadata
        
    except Exception as e:
        print(f"Error checking repository {repo_url}: {e}")
        return False, None

def _parse_mod_conf(content):
    """Parse mod.conf content and extract metadata"""
    metadata = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            if key == 'name':
                metadata['name'] = value
            elif key == 'description':
                metadata['description'] = value
            elif key == 'depends':
                metadata['depends'] = [dep.strip() for dep in value.split(',') if dep.strip()]
            elif key == 'optional_depends':
                metadata['optional_depends'] = [dep.strip() for dep in value.split(',') if dep.strip()]
            elif key == 'author':
                metadata['author'] = value
            elif key == 'title':
                metadata['title'] = value
            elif key == 'min_minetest_version' or key == 'min_luanti_version':
                metadata['min_version'] = value
            elif key == 'max_minetest_version' or key == 'max_luanti_version':
                metadata['max_version'] = value
    
    metadata['type'] = 'mod'
    return metadata

def _parse_game_conf(content):
    """Parse game.conf content and extract metadata"""
    metadata = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            if key == 'name':
                metadata['name'] = value
            elif key == 'description':
                metadata['description'] = value
            elif key == 'author':
                metadata['author'] = value
            elif key == 'title':
                metadata['title'] = value
    
    metadata['type'] = 'game'
    return metadata

def get_repository_info(repo_url):
    """Get basic repository information (for GitHub/GitLab)"""
    try:
        if 'github.com' in repo_url:
            match = re.match(r'https://github\.com/([\w\-\.]+)/([\w\-\.]+)/?', repo_url)
            if match:
                owner, repo = match.groups()
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'name': data.get('name', ''),
                        'description': data.get('description', ''),
                        'owner': data.get('owner', {}).get('login', ''),
                        'stars': data.get('stargazers_count', 0),
                        'forks': data.get('forks_count', 0),
                        'language': data.get('language', ''),
                        'topics': data.get('topics', []),
                        'created_at': data.get('created_at', ''),
                        'updated_at': data.get('updated_at', ''),
                    }
        
        elif 'gitlab.com' in repo_url:
            match = re.match(r'https://gitlab\.com/([\w\-\.]+/[\w\-\.]+)/?', repo_url)
            if match:
                project_path = match.group(1)
                api_url = f"https://gitlab.com/api/v4/projects/{project_path.replace('/', '%2F')}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'name': data.get('name', ''),
                        'description': data.get('description', ''),
                        'owner': data.get('owner', {}).get('username', ''),
                        'stars': data.get('star_count', 0),
                        'forks': data.get('forks_count', 0),
                        'topics': data.get('topics', []),
                        'created_at': data.get('created_at', ''),
                        'updated_at': data.get('last_activity_at', ''),
                    }
    
    except Exception as e:
        print(f"Error getting repository info for {repo_url}: {e}")
    
    return {}
