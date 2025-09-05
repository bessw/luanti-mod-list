# Luanti Mod Search System

A comprehensive system for discovering and cataloging Luanti (formerly Minetest) mods, games, and modpacks from multiple sources including ContentDB, forum posts, and git repositories.

## Features

### 🔍 Multi-Source Discovery
- **ContentDB API**: Search the official Luanti Content Database
- **Forum Scraping**: Extract mod information from Luanti forum posts
- **Git Repository Analysis**: Automatically detect Luanti mods in git repositories
- **Work Queue System**: Efficiently process large numbers of items

### 🏗️ Architecture
- **SQLite Databases**: Separate databases for mod data, work queues, and metadata
- **Work Queues**: Forum threads and git repositories are processed asynchronously
- **Git Host Discovery**: Automatically discovers and tracks self-hosted git instances
- **Duplicate Prevention**: Avoids reprocessing already known items

### 🧪 Comprehensive Testing
- Unit tests for all major components
- Mock-based testing for external API calls
- Test coverage for work queue management

## Installation

1. Clone the repository
2. Install required dependencies:
```bash
pip install requests beautifulsoup4
```

## Quick Start

### 1. Initialize the System
```bash
python mod_search.py
```
This will:
- Initialize all databases
- Search ContentDB for mods, games, and texture packs
- Fetch forum thread lists and add them to work queues
- Search GitHub for Luanti-related repositories

### 2. Process Work Queues
```bash
# Check work queue status
python work_queue_manager.py status

# Refresh forum thread lists
python work_queue_manager.py refresh-forum

# Process forum threads (finds git repositories)
python work_queue_manager.py process-forum --batch-size 10 --max-batches 5

# Process git repositories (validates as Luanti mods)
python work_queue_manager.py process-git --batch-size 10 --max-batches 3
```

## Database Schema

### Main Results Database (`mod_list.db`)
Stores discovered mods, games, and modpacks with metadata:
- Basic info: name, title, description, author, type
- URLs: ContentDB, forum, repository, website
- Metadata: tags, dependencies, license, version requirements
- Source tracking: where the item was discovered

### Work Queue Databases
- `forum_queue.db`: Forum threads to be processed
- `git_queue.db`: Git repositories to be validated
- `git_hosts.db`: Discovered self-hosted git instances
- `non_mod_repos.db`: Repositories known to not contain Luanti content

## API Reference

### Forum Search Functions

```python
from forum_search import fetch_forum_thread_list, process_forum_work_queue

# Fetch forum threads and add to work queue
threads = fetch_forum_thread_list("https://forum.luanti.org/viewforum.php?f=11")

# Process work queue
results = process_forum_work_queue(batch_size=10)
```

### Git Utilities

```python
from git_utils import is_git_repository_url, check_luanti_mod_repository

# Check if URL is a git repository
is_git, host_type = is_git_repository_url("https://github.com/user/repo")

# Validate if repository contains a Luanti mod
is_mod, metadata = check_luanti_mod_repository("https://github.com/user/luanti-mod")
```

### Database Operations

```python
from db_utils import (init_db, add_forum_thread_to_queue, 
                      get_unprocessed_forum_threads, save_result)

# Initialize all databases
init_db()

# Add items to work queues
add_forum_thread_to_queue(url, title, thread_type)

# Get unprocessed items
threads = get_unprocessed_forum_threads(limit=10)

# Save discovered mod/game
save_result(mod_data, source="forum")
```

## Git Repository Detection

The system can detect and validate Luanti content in repositories from multiple git hosting providers:

### Supported Git Hosts
- **GitHub** (github.com)
- **GitLab** (gitlab.com and self-hosted instances)
- **Codeberg** (codeberg.org)
- **Bitbucket** (bitbucket.org)
- **Gitea/Forgejo** (self-hosted instances)
- **SourceForge** (sourceforge.net)
- **Generic .git URLs**

### Validation Process
1. **mod.conf Detection**: Looks for `mod.conf` file (Luanti mods)
2. **game.conf Detection**: Looks for `game.conf` file (Luanti games)  
3. **Modpack Detection**: Checks for `mods/` directory structure
4. **Metadata Extraction**: Parses configuration files for mod information

## Work Queue Management

The system uses work queues to efficiently process large numbers of forum threads and git repositories:

### Forum Thread Processing
1. Scrape forum pages for thread lists
2. Add threads to work queue (avoiding duplicates)
3. Process threads to extract git repository links
4. Validate repositories as Luanti content
5. Save results to main database

### Git Repository Processing
1. Receive repositories from forum processing or direct search
2. Add to git work queue
3. Check if repository contains Luanti content
4. Extract mod/game metadata
5. Save to main database or mark as non-mod

## Testing

Run the comprehensive test suite:

```bash
# Test forum search functionality
python -m unittest test_forum_search.py -v

# Test git utilities
python -m unittest test_git_utils.py -v

# Test ContentDB integration
python -m unittest test_contentdb_api.py -v
```

## Configuration

### Forum URLs
- Mod Releases: `https://forum.luanti.org/viewforum.php?f=11`
- Games: `https://forum.luanti.org/viewforum.php?f=15`

### GitHub Search Terms
- Query terms: `["luanti", "minetest"]`
- Topics: `["luanti-mod", "minetest-mod"]`

### Batch Processing Limits
- Default batch size: 10 items
- Configurable via command line arguments
- Rate limiting to avoid overwhelming servers

## Error Handling

- **Network Timeouts**: Configurable timeouts for API calls
- **Rate Limiting**: Built-in delays to respect server limits  
- **Duplicate Detection**: Prevents reprocessing known items
- **Error Logging**: Tracks failed processing attempts
- **Graceful Degradation**: Continues processing if individual items fail

## Development

### Adding New Git Hosts
1. Add URL pattern to `git_utils.py`
2. Implement API integration if available
3. Add to test cases
4. Update documentation

### Extending Search Sources
1. Create new search module
2. Implement work queue integration
3. Add database schema updates
4. Write comprehensive tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]

## Changelog

### v1.0.0 (Current)
- ✅ Work queue system for forum threads and git repositories
- ✅ Multi-source mod discovery (ContentDB, forums, GitHub)
- ✅ Git repository validation for Luanti content
- ✅ Self-hosted git instance discovery
- ✅ Comprehensive test suite
- ✅ Command-line work queue manager
- ✅ Duplicate detection and prevention
- ✅ Support for mods, games, and modpacks

## Future Enhancements

- Web interface for browsing discovered mods
- Integration with additional git hosting providers
- Mod dependency analysis and visualization
- Automated mod compatibility checking
- RSS/webhook notifications for new discoveries
- Integration with mod managers and launchers
