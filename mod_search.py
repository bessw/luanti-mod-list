#!/usr/bin/env python3
"""
Luanti Mod Search System

This script orchestrates the search for Luanti mods from multiple sources:
1. ContentDB - Official mod repository
2. Forum - Community forum threads
3. Git repositories - GitHub, GitLab, Gitea, etc.
"""

import argparse
import sys
from contentdb.api import sync_contentdb_to_database
from forum.search import fetch_forum_thread_list, process_forum_work_queue
from git.search import search_all_git_servers, process_git_work_queue
from db_utils import (
    init_all_databases, get_mod_count, get_forum_queue_status, get_git_queue_status
)


def main():
    """Main function to orchestrate the mod search"""
    parser = argparse.ArgumentParser(description='Luanti Mod Search System')
    parser.add_argument('--contentdb', action='store_true',
                       help='Sync ContentDB packages')
    parser.add_argument('--forum', action='store_true',
                       help='Fetch forum threads and process queue')
    parser.add_argument('--git-search', action='store_true',
                       help='Search git repositories across all servers')
    parser.add_argument('--git-process', action='store_true',
                       help='Process git work queue for Luanti mods')
    parser.add_argument('--all', action='store_true',
                       help='Run all search operations')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for processing work queues')
    
    args = parser.parse_args()
    
    # Initialize all databases
    print("Initializing databases...")
    init_all_databases()
    
    print("=== Luanti Mod Search System ===")
    
    # Show current status
    mod_count = get_mod_count()
    forum_status = get_forum_queue_status()
    git_status = get_git_queue_status()
    
    print(f"\nCurrent Status:")
    print(f"  Mods in database: {mod_count}")
    print(f"  Forum queue: {forum_status.get('pending', 0)} pending, {forum_status.get('processed', 0)} processed")
    print(f"  Git queue: {git_status.get('pending', 0)} pending, {git_status.get('processed', 0)} processed")
    
    # Run selected operations
    if args.contentdb or args.all:
        print("\n1. Syncing ContentDB...")
        added, updated = sync_contentdb_to_database()
        print(f"   ContentDB sync complete: {added} added, {updated} updated")
    
    if args.forum or args.all:
        print("\n2. Forum search and processing...")
        
        # Fetch forum thread lists
        print("   Fetching forum thread lists...")
        
        # Mod releases forum
        mod_forum_url = "https://forum.luanti.org/viewforum.php?f=11"
        added_mod_threads = fetch_forum_thread_list(mod_forum_url)
        print(f"   Added {len(added_mod_threads)} mod/modpack threads to queue")
        
        # Games forum  
        games_forum_url = "https://forum.luanti.org/viewforum.php?f=15"
        added_game_threads = fetch_forum_thread_list(games_forum_url, thread_types=["[game]"])
        print(f"   Added {len(added_game_threads)} game threads to queue")
        
        # Process forum work queue
        print("   Processing forum work queue...")
        total_processed = 0
        batch_count = 0
        max_batches = 5  # Limit to avoid overwhelming
        
        while batch_count < max_batches:
            results = process_forum_work_queue(args.batch_size)
            if not results:
                break
            
            total_processed += len(results)
            successful_results = [r for r in results if r.get("status") == "success"]
            total_mods_found = sum(r.get("luanti_mods_found", 0) for r in successful_results)
            total_git_repos = sum(r.get("git_repos_found", 0) for r in successful_results)
            
            print(f"   Batch {batch_count + 1}: Processed {len(results)} threads")
            print(f"     Found {total_git_repos} git repos, {total_mods_found} Luanti mods")
            
            batch_count += 1
        
        print(f"   Forum processing: {total_processed} threads processed")
    
    if args.git_search or args.all:
        print("\n3. Git repository search...")
        keywords = ['luanti', 'minetest']
        repositories = search_all_git_servers(keywords, max_results_per_host=50)
        print(f"   Found {len(repositories)} repositories across all git servers")
    
    if args.git_process or args.all:
        print("\n4. Processing git work queue...")
        process_git_work_queue(args.batch_size)
        print("   Git queue processing complete")
    
    # Show final status
    final_mod_count = get_mod_count()
    final_forum_status = get_forum_queue_status()
    final_git_status = get_git_queue_status()
    
    print(f"\nFinal Status:")
    print(f"  Mods in database: {final_mod_count} (+" + str(final_mod_count - mod_count) + ")")
    print(f"  Forum queue: {final_forum_status.get('pending', 0)} pending, {final_forum_status.get('processed', 0)} processed")
    print(f"  Git queue: {final_git_status.get('pending', 0)} pending, {final_git_status.get('processed', 0)} processed")
    
    print("\n=== Search Complete ===")
    print("\nNext steps:")
    print("- Run with --forum to process more forum threads")
    print("- Run with --git-process to validate more git repositories")
    print("- Use work_queue_manager.py to manage work queues")
    print("- Analyze results in the mod_list.db database")


if __name__ == "__main__":
    main()