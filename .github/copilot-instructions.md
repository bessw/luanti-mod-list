# Luanti Mod Search System

The Luanti Mod Search System is a Python application that discovers and catalogs Luanti (formerly Minetest) mods, games, and modpacks from multiple sources: ContentDB (official repository), community forum threads, and git repositories across various hosting platforms.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the information provided here.**

## Working Effectively

### Environment Setup
Run these commands in order. **NEVER CANCEL** any command - let them complete fully:

```bash
# Install Python dependencies
pip3 install -r requirements.txt
# Takes 15-30 seconds normally, NEVER CANCEL - set timeout to 60+ seconds
```

### Database Initialization  
**ALWAYS** initialize databases before any operations:
```bash
python3 -c "from db_utils import init_all_databases; init_all_databases(); print('Databases initialized')"
# Takes < 1 second, creates SQLite databases: mod_list.db, forum_queue.db, git_queue.db, git_hosts.db, non_mod_repos.db
```

### Core Operations

#### ContentDB Sync (requires network access)
```bash  
python3 -c "from contentdb.api import sync_contentdb_to_database; print('Result:', sync_contentdb_to_database())"
# Takes 10-60 seconds depending on network, NEVER CANCEL - set timeout to 120+ seconds
```

#### Work Queue Status
```bash
python3 -c "
from db_utils import get_unprocessed_forum_threads, get_unprocessed_git_repos
print('Forum threads pending:', len(get_unprocessed_forum_threads(1000)))  
print('Git repos pending:', len(get_unprocessed_git_repos(1000)))
"
# Takes < 1 second
```

#### Database Operations Testing
```bash
python3 -c "
import db_utils
db_utils.init_all_databases()
# Test adding items to queues
db_utils.add_forum_thread_to_queue('test_url', 'test_title', 'mod')  
db_utils.add_git_repo_to_queue('https://github.com/test/repo', 'test_source')
print('Database operations working correctly')
"
# Takes < 1 second
```

## Known Issues and Workarounds

### Import Errors - CRITICAL INFORMATION
The codebase has missing modules that cause import errors:
- `git.search` module is missing - causes `mod_search.py` to fail  
- `git.utils` module is missing - causes `work_queue_manager.py` to fail
- **DO NOT** try to run these scripts directly until the missing modules are implemented

### Working Components
These components work correctly:
- `db_utils.py` - All database operations
- `contentdb/api.py` - ContentDB integration (with network)
- `forum/search.py` - Forum processing functions  
- `git/github_web.py`, `git/gitlab_web.py` - Git repository interfaces
- Database initialization and basic operations

### Network Requirements
- **ContentDB operations require internet access** to content.minetest.net
- **Git operations require access** to GitHub API, GitLab API, etc.
- **Forum processing requires access** to forum.luanti.org
- In restricted environments, these operations will fail with connection errors

## Testing

### Running Tests
**IMPORTANT**: Tests require network access and will fail in restricted environments:

```bash
# Test database operations (works offline)
python3 -c "import db_utils; db_utils.init_all_databases(); print('Database tests pass')"

# Test ContentDB API (requires network)  
python3 -m unittest tests.test_contentdb_api -v
# EXPECTED: May fail with ConnectionError in restricted networks

# Test git web interfaces (requires network)
python3 -m unittest tests.test_git_web -v  
# EXPECTED: May fail with GitHub API rate limits or connection errors

# Test forum search (requires network)
python3 -m unittest tests.test_forum_search -v
# EXPECTED: May fail with forum.luanti.org connection errors
```

### Manual Validation Scenarios
After making changes, **ALWAYS** test these scenarios:

1. **Database Operations**:
   ```bash
   python3 -c "
   import db_utils, uuid
   db_utils.init_all_databases()
   # Test forum queue with unique URL to avoid duplicates
   unique_id = str(uuid.uuid4())[:8]
   success = db_utils.add_forum_thread_to_queue(f'https://example.com/thread-{unique_id}', 'Test Mod', 'mod')
   assert success, 'Forum thread addition failed'
   threads = db_utils.get_unprocessed_forum_threads(10)
   assert len(threads) > 0, 'No threads in queue'
   # Test git queue with unique URL to avoid duplicates  
   success = db_utils.add_git_repo_to_queue(f'https://github.com/test/repo-{unique_id}', 'github')
   assert success, 'Git repo addition failed'
   repos = db_utils.get_unprocessed_git_repos(10)
   assert len(repos) > 0, 'No repos in queue'
   print('All database operations validated successfully')
   "
   ```

2. **ContentDB Integration** (requires network):
   ```bash
   python3 -c "
   from contentdb.api import fetch_all_packages
   try:
       packages = fetch_all_packages()
       print(f'ContentDB returned {len(packages)} packages')
       assert isinstance(packages, list), 'Invalid package format'  
   except Exception as e:
       print(f'ContentDB failed (expected in restricted networks): {e}')
   "
   ```

## Timing Expectations and Timeouts

### Fast Operations (< 1 second)
- Database initialization: `init_all_databases()`
- Adding items to work queues: `add_forum_thread_to_queue()`, `add_git_repo_to_queue()`
- Querying work queue status: `get_unprocessed_*()` functions
- Basic database operations

### Medium Operations (10-60 seconds) 
- **NEVER CANCEL** - Always set timeout to 120+ seconds:
- Dependency installation: `pip3 install -r requirements.txt`
- ContentDB sync: `sync_contentdb_to_database()` 
- Individual API calls to git repositories

### Potentially Long Operations (2-10+ minutes)
- **NEVER CANCEL** - Always set timeout to 15+ minutes:
- Full ContentDB package processing with large datasets
- Batch forum thread processing: `process_forum_work_queue()`
- Git repository validation across multiple hosts
- Large work queue processing operations

**CRITICAL**: Always use appropriate timeout values. Network operations can be slow and canceling prematurely will cause incomplete results.

## Repository Structure

### Key Directories
```
/
├── .github/           # GitHub configuration and this file
├── contentdb/         # ContentDB API integration
│   ├── api.py        # Main ContentDB functions
│   └── __init__.py
├── forum/             # Forum scraping and processing  
│   ├── search.py     # Forum thread processing
│   └── __init__.py
├── git/               # Git repository interfaces
│   ├── git_web.py    # Abstract base class
│   ├── github_web.py # GitHub API integration
│   ├── gitlab_web.py # GitLab API integration  
│   ├── gitea_forgejo_web.py # Gitea/Forgejo support
│   └── __init__.py
├── tests/             # Test suite
│   ├── test_contentdb_api.py
│   ├── test_forum_search.py
│   └── test_git_web.py
├── db_utils.py        # Database operations
├── mod_search.py      # Main entry point (HAS IMPORT ERRORS)
├── work_queue_manager.py # Work queue management (HAS IMPORT ERRORS) 
└── requirements.txt   # Python dependencies
```

### Key Files to Check When Making Changes
- **Always check `db_utils.py`** after modifying database schema
- **Always check `contentdb/api.py`** after modifying ContentDB integration
- **Always test database initialization** after changing `init_all_databases()`
- **Always verify imports** in modules under `git/`, `forum/`, `contentdb/`

## Validation Requirements

### Before Committing Changes
Always run these validation steps:

```bash  
# 1. Test dependency installation
pip3 install -r requirements.txt

# 2. Test database operations  
python3 -c "
import db_utils
db_utils.init_all_databases()  
print('✓ Database initialization works')
"

# 3. Test basic imports (some will fail - this is expected)
python3 -c "
try:
    import contentdb.api
    print('✓ ContentDB module imports correctly')
except Exception as e:
    print('✗ ContentDB import failed:', e)

try:  
    import forum.search
    print('✓ Forum module imports correctly')
except Exception as e:
    print('✗ Forum import failed:', e)

try:
    from git.git_web import GitWeb
    print('✓ Git web module imports correctly') 
except Exception as e:
    print('✗ Git web import failed:', e)
"

# 4. Run available tests
python3 -c "
import unittest
# Load tests that don't require network
loader = unittest.TestLoader()
suite = unittest.TestSuite()
try:
    # Add tests here that work offline
    from tests import test_forum_search
    print('✓ Test modules can be imported')
except Exception as e:
    print('✗ Test import failed:', e)
"
```

### Common Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'git.search'`
**Solution**: This module is missing from the codebase. The `mod_search.py` script cannot run until this is implemented.

**Problem**: `ModuleNotFoundError: No module named 'git.utils'`  
**Solution**: This module is missing from the codebase. The `work_queue_manager.py` script cannot run until this is implemented.

**Problem**: Network connection errors during ContentDB or git operations
**Solution**: Expected in restricted environments. Operations will fail gracefully and return empty results.

**Problem**: GitHub API rate limiting in tests
**Solution**: Expected behavior. Tests may need to be run with API tokens in some environments.

## Development Guidelines

### When Adding New Features
1. **Always initialize databases first**: `python3 -c "from db_utils import init_all_databases; init_all_databases()"`
2. **Test database operations work**: Add test data to queues and verify retrieval  
3. **Check imports resolve**: Ensure all your imports exist and work
4. **Test with network restrictions**: Code should handle connection failures gracefully
5. **Set appropriate timeouts**: Use 60+ seconds for network operations, 15+ minutes for batch processing

### When Debugging Issues  
1. **Test database operations first** - they're fast and should always work
2. **Check for missing modules** - several `git.*` modules are incomplete  
3. **Verify network access** - many features require external API access
4. **Check API rate limits** - GitHub, GitLab APIs may be restricted
5. **Use LONG TIMEOUTS** - never cancel operations prematurely

**REMEMBER**: This system is designed for discovering and cataloging Luanti mods across multiple platforms. Core functionality works but some integration modules are incomplete.