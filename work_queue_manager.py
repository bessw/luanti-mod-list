"""
Work Queue Manager - Utility script for managing forum and git work queues
"""
import argparse
import sys
from db_utils import (
    init_all_databases, get_unprocessed_forum_threads, get_unprocessed_git_repos,
    mark_forum_thread_processed, mark_git_repo_processed, 
    get_git_hosts, is_known_non_mod_repo, save_result
)
from forum.search import process_forum_work_queue, fetch_forum_thread_list
from git.utils import check_luanti_mod_repository, get_repository_info
from git.search import process_git_work_queue

def show_queue_status():
    """Show current status of work queues"""
    print("=== Work Queue Status ===")
    
    # Forum queue status
    forum_threads = get_unprocessed_forum_threads(1000)  # Get up to 1000 to count
    print(f"Forum threads pending: {len(forum_threads)}")
    
    if forum_threads:
        thread_types = {}
        for _, _, _, thread_type in forum_threads:
            thread_types[thread_type] = thread_types.get(thread_type, 0) + 1
        
        for thread_type, count in thread_types.items():
            print(f"  - {thread_type}: {count} threads")
    
    # Git queue status
    git_repos = get_unprocessed_git_repos(1000)  # Get up to 1000 to count
    print(f"Git repositories pending: {len(git_repos)}")
    
    # Git hosts discovered
    git_hosts = get_git_hosts()
    print(f"Git hosts discovered: {len(git_hosts)}")
    
    if git_hosts:
        host_types = {}
        for _, host_type in git_hosts:
            host_types[host_type] = host_types.get(host_type, 0) + 1
        
        for host_type, count in host_types.items():
            print(f"  - {host_type}: {count} hosts")

def process_forum_queue(batch_size=10, max_batches=None):
    """Process forum work queue"""
    print(f"=== Processing Forum Queue (batch size: {batch_size}) ===")
    
    total_processed = 0
    batch_count = 0
    
    while True:
        if max_batches and batch_count >= max_batches:
            print(f"Reached maximum batch limit ({max_batches})")
            break
            
        results = process_forum_work_queue(batch_size)
        if not results:
            print("No more threads to process")
            break
        
        batch_count += 1
        total_processed += len(results)
        
        successful_results = [r for r in results if r.get("status") == "success"]
        error_results = [r for r in results if r.get("status") == "error"]
        total_mods_found = sum(r.get("luanti_mods_found", 0) for r in successful_results)
        total_git_repos = sum(r.get("git_repos_found", 0) for r in successful_results)
        
        print(f"Batch {batch_count}:")
        print(f"  - Processed: {len(results)} threads")
        print(f"  - Successful: {len(successful_results)}")
        print(f"  - Errors: {len(error_results)}")
        print(f"  - Git repos found: {total_git_repos}")
        print(f"  - Luanti mods found: {total_mods_found}")
        
        if error_results:
            print("  - Errors:")
            for error_result in error_results[:3]:  # Show first 3 errors
                print(f"    * {error_result.get('title', 'Unknown')}: {error_result.get('message', 'Unknown error')}")
        
        print()
    
    print(f"Total threads processed: {total_processed}")

def process_git_queue(batch_size=10, max_batches=None):
    """Process git repository work queue using the new modular system"""
    print(f"=== Processing Git Repository Queue (batch size: {batch_size}) ===")
    
    batch_count = 0
    
    while True:
        if max_batches and batch_count >= max_batches:
            print(f"Reached maximum batch limit ({max_batches})")
            break
        
        # Use the new modular git search system
        process_git_work_queue(batch_size)
        batch_count += 1
        
        # Check if there are more repositories to process
        remaining_repos = get_unprocessed_git_repos(1)
        if not remaining_repos:
            print("No more repositories to process")
            break
        
        print(f"Completed batch {batch_count}")
    
    print(f"Processed {batch_count} batches")

def refresh_forum_threads():
    """Refresh forum thread lists"""
    print("=== Refreshing Forum Thread Lists ===")
    
    forums = [
        ("https://forum.luanti.org/viewforum.php?f=11", "Mod Releases", ["[mod]", "[modpack]"]),
        ("https://forum.luanti.org/viewforum.php?f=15", "Games", ["[game]"]),
    ]
    
    total_added = 0
    
    for forum_url, forum_name, thread_types in forums:
        print(f"Fetching from {forum_name} forum...")
        added_threads = fetch_forum_thread_list(forum_url, thread_types)
        print(f"  Added {len(added_threads)} new threads to queue")
        total_added += len(added_threads)
    
    print(f"Total new threads added: {total_added}")

def main():
    parser = argparse.ArgumentParser(description="Luanti Mod Search Work Queue Manager")
    parser.add_argument("action", choices=["status", "process-forum", "process-git", "refresh-forum"],
                       help="Action to perform")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Number of items to process in each batch (default: 10)")
    parser.add_argument("--max-batches", type=int,
                       help="Maximum number of batches to process")
    
    args = parser.parse_args()
    
    # Initialize database
    init_all_databases()
    
    if args.action == "status":
        show_queue_status()
    elif args.action == "process-forum":
        process_forum_queue(args.batch_size, args.max_batches)
    elif args.action == "process-git":
        process_git_queue(args.batch_size, args.max_batches)
    elif args.action == "refresh-forum":
        refresh_forum_threads()

if __name__ == "__main__":
    main()
