import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import sys
import os
from git.git_web import GitWeb

# Add parent directory to path to import db_utils and git_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_utils import (forum_url_exists, save_result, add_forum_thread_to_queue, 
                      forum_thread_in_queue, get_unprocessed_forum_threads, 
                      mark_forum_thread_processed, add_git_repo_to_queue)


"""
Example HTML structure of the forum website can be found in forum_example
"""

def fetch_forum_thread_list(forum_url="https://forum.luanti.org/viewforum.php?f=11", thread_types=None):
    """
    Fetch list of forum threads and add them to work queue.
    
    Args:
        forum_url: URL of the forum section
        thread_types: List of thread types to look for (e.g., ["[mod]", "[game]", "[modpack]"])
    
    Returns:
        List of thread URLs added to queue
    """
    if thread_types is None:
        thread_types = ["[mod]", "[mod pack]", "[modpack]", "[game]"]
    
    resp = requests.get(forum_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    added_threads = []
    
    for topic in soup.select(".topictitle"):
        title = topic.text.strip()
        link = topic.get("href")
        
        if not link.startswith("http"):
            link = urljoin(forum_url, link)
        
        # Determine thread type
        thread_type = "unknown"
        title_lower = title.lower()
        
        if any(prefix in title_lower for prefix in ["[mod]"]):
            thread_type = "mod"
        elif any(prefix in title_lower for prefix in ["[mod pack]", "[modpack]"]):
            thread_type = "modpack"
        elif "[game]" in title_lower:
            thread_type = "game"
        
        # Add to work queue if not already present
        if not forum_thread_in_queue(link) and not forum_url_exists(link):
            if add_forum_thread_to_queue(link, title, thread_type):
                added_threads.append(link)
    
    return added_threads

def process_forum_thread(thread_id, forum_url, title, thread_type):
    """
    Process a single forum thread from the work queue.
    Finds all git repository links in the first post and processes them.
    
    Args:
        thread_id: Database ID of the thread
        forum_url: URL of the forum thread
        title: Title of the thread
        thread_type: Type of thread (mod, modpack, game, unknown)
    
    Returns:
        Dictionary with processing results
    """
    try:
        resp = requests.get(forum_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the first post content
        first_post = soup.select_one(".post .content")
        if not first_post:
            mark_forum_thread_processed(thread_id)
            return {"status": "error", "message": "Could not find first post content"}
        
        # Extract all links from the first post
        links = first_post.find_all("a", href=True)
        git_repos_found = []
        luanti_mods_found = []
        
        for link in links:
            href = link.get("href")
            if not href:
                continue
            
            # Convert relative URLs to absolute
            if not href.startswith("http"):
                href = urljoin(forum_url, href)
            
            # Check if it's a git repository
            is_git = False
            try:
                is_git = GitWeb.is_git_server(href)
            except Exception:
                is_git = False
            if is_git:
                git_repos_found.append(href)
                
                # Add to git work queue
                add_git_repo_to_queue(href, f"forum:{forum_url}")
                
                # Check if it's a Luanti mod
                is_mod, mod_metadata = check_luanti_mod_repository(href)
                if is_mod:
                    # Create result entry
                    result = {
                        "forum_url": forum_url,
                        "repo_url": href,
                        "title": title,
                        "name": mod_metadata.get("name", title),
                        "description": mod_metadata.get("description", ""),
                        "author": mod_metadata.get("author", ""),
                        "type": mod_metadata.get("type", thread_type),
                        "short_description": mod_metadata.get("description", ""),
                    }
                    
                    # Add any additional metadata
                    if "depends" in mod_metadata:
                        result["dependencies"] = ",".join(mod_metadata["depends"])
                    if "optional_depends" in mod_metadata:
                        result["optional_dependencies"] = ",".join(mod_metadata["optional_depends"])
                    
                    save_result(result, "forum")
                    luanti_mods_found.append(result)
        
        # Mark thread as processed
        mark_forum_thread_processed(thread_id)
        
        return {
            "status": "success",
            "git_repos_found": len(git_repos_found),
            "luanti_mods_found": len(luanti_mods_found),
            "repos": git_repos_found,
            "mods": luanti_mods_found
        }
        
    except Exception as e:
        print(f"Error processing forum thread {forum_url}: {e}")
        return {"status": "error", "message": str(e)}

def process_forum_work_queue(batch_size=10):
    """
    Process a batch of forum threads from the work queue.
    
    Args:
        batch_size: Number of threads to process in this batch
    
    Returns:
        List of processing results
    """
    threads = get_unprocessed_forum_threads(batch_size)
    results = []
    
    for thread_id, forum_url, title, thread_type in threads:
        result = process_forum_thread(thread_id, forum_url, title, thread_type)
        result["thread_id"] = thread_id
        result["forum_url"] = forum_url
        result["title"] = title
        results.append(result)
    
    return results

# Legacy functions for backward compatibility
def search_forum_mods(query, forum_url="https://forum.luanti.org/viewforum.php?f=11"):
    """Legacy function - use fetch_forum_thread_list instead"""
    resp = requests.get(forum_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    mods = []
    for topic in soup.select(".topictitle"):
        title = topic.text.strip()
        link = topic.get("href")
        if any(prefix in title.lower() for prefix in ["[mod]", "[mod pack]"]):
            if query.lower() in title.lower() or query in ["mod", "modpack"]:
                if not link.startswith("http"):
                    link = urljoin(forum_url, link)
                mods.append({"title": title, "url": link})
    return mods

def search_forum_games(forum_url="https://forum.luanti.org/viewforum.php?f=15"):
    """Legacy function - use fetch_forum_thread_list instead"""
    resp = requests.get(forum_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    games = []
    for topic in soup.select(".topictitle"):
        title = topic.text.strip()
        link = topic.get("href")
        if "[game]" in title.lower():
            if not link.startswith("http"):
                link = urljoin(forum_url, link)
            games.append({"title": title, "url": link, "type": "game"})
    return games
