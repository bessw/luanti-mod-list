import sqlite3
import json

DB_PATH = "mod_list.db"
FORUM_QUEUE_DB = "forum_queue.db"
GIT_QUEUE_DB = "git_queue.db"
GIT_HOSTS_DB = "git_hosts.db"
NON_MOD_REPOS_DB = "non_mod_repos.db"

def init_all_databases():
    """Initialize all databases"""
    init_db()
    init_git_work_queue()

def init_db():
    # Initialize main mod list database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contentdb_url TEXT,
            forum_url TEXT,
            repo_url TEXT,
            name TEXT,
            short_description TEXT,
            dev_state TEXT,
            tags TEXT,
            content_warnings TEXT,
            license TEXT,
            media_license TEXT,
            long_description TEXT,
            website TEXT,
            issue_tracker TEXT,
            video_url TEXT,
            donate_url TEXT,
            translation_url TEXT,
            source TEXT,
            type TEXT,
            title TEXT,
            author TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

    # Initialize forum work queue database
    conn = sqlite3.connect(FORUM_QUEUE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS forum_threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forum_url TEXT UNIQUE,
            title TEXT,
            type TEXT,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Initialize git work queue database
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS git_repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT UNIQUE,
            source TEXT,
            processed INTEGER DEFAULT 0,
            is_luanti_mod INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Initialize git hosts database
    conn = sqlite3.connect(GIT_HOSTS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS git_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_url TEXT UNIQUE,
            host_type TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Initialize non-mod repos database
    conn = sqlite3.connect(NON_MOD_REPOS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS non_mod_repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT UNIQUE,
            reason TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_result(item, source):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO results (contentdb_url, forum_url, repo_url, name, short_description, dev_state, tags, content_warnings, license, media_license, long_description, website, issue_tracker, video_url, donate_url, translation_url, source, type, title, author, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
        item.get("contentdb_url", ""),
        item.get("forum_url", ""),
        item.get("repo_url", ""),
        item.get("name", ""),
        item.get("short_description", ""),
        item.get("dev_state", ""),
        ",".join(item.get("tags", [])),
        ",".join(item.get("content_warnings", [])),
        item.get("license", ""),
        item.get("media_license", ""),
        item.get("long_description", ""),
        item.get("website", ""),
        item.get("issue_tracker", ""),
        item.get("video_url", ""),
        item.get("donate_url", ""),
        item.get("translation_url", ""),
        source,
        item.get("type", "unknown"),
        item.get("title", item.get("name", "")),
        item.get("author", item.get("owner", {}).get("login", "")),
        item.get("description", "")
    ))
    conn.commit()
    conn.close()

def forum_url_exists(forum_url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM results WHERE forum_url=?", (forum_url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def contentdb_url_exists(contentdb_url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM results WHERE contentdb_url=?", (contentdb_url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Forum queue functions
def add_forum_thread_to_queue(forum_url, title, thread_type):
    """Add a forum thread to the work queue"""
    conn = sqlite3.connect(FORUM_QUEUE_DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO forum_threads (forum_url, title, type) VALUES (?, ?, ?)", 
                 (forum_url, title, thread_type))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Thread already exists
        return False
    finally:
        conn.close()

def get_unprocessed_forum_threads(limit=10):
    """Get unprocessed forum threads from the queue"""
    conn = sqlite3.connect(FORUM_QUEUE_DB)
    c = conn.cursor()
    c.execute("SELECT id, forum_url, title, type FROM forum_threads WHERE processed=0 LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results

def mark_forum_thread_processed(thread_id):
    """Mark a forum thread as processed"""
    conn = sqlite3.connect(FORUM_QUEUE_DB)
    c = conn.cursor()
    c.execute("UPDATE forum_threads SET processed=1 WHERE id=?", (thread_id,))
    conn.commit()
    conn.close()

def forum_thread_in_queue(forum_url):
    """Check if a forum thread is already in the queue"""
    conn = sqlite3.connect(FORUM_QUEUE_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM forum_threads WHERE forum_url=?", (forum_url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Git queue functions
def add_git_repo_to_queue(repo_url, source):
    """Add a git repo to the work queue"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO git_repos (repo_url, source) VALUES (?, ?)", 
                 (repo_url, source))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Repo already exists
        return False
    finally:
        conn.close()

def get_unprocessed_git_repos(limit=10):
    """Get unprocessed git repos from the queue"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("SELECT id, repo_url, source FROM git_repos WHERE processed=0 LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results

def mark_git_repo_processed(repo_id, is_luanti_mod=None):
    """Mark a git repo as processed"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("UPDATE git_repos SET processed=1, is_luanti_mod=? WHERE id=?", 
             (is_luanti_mod, repo_id))
    conn.commit()
    conn.close()

def git_repo_in_queue(repo_url):
    """Check if a git repo is already in the queue"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM git_repos WHERE repo_url=?", (repo_url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Git hosts functions
def add_git_host(host_url, host_type):
    """Add a discovered git host"""
    conn = sqlite3.connect(GIT_HOSTS_DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO git_hosts (host_url, host_type) VALUES (?, ?)", 
                 (host_url, host_type))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Host already exists
        return False
    finally:
        conn.close()

def get_git_hosts():
    """Get all discovered git hosts"""
    conn = sqlite3.connect(GIT_HOSTS_DB)
    c = conn.cursor()
    c.execute("SELECT host_url, host_type FROM git_hosts")
    results = c.fetchall()
    conn.close()
    return results

# Non-mod repos functions
def add_non_mod_repo(repo_url, reason):
    """Add a repo known to not be a mod"""
    conn = sqlite3.connect(NON_MOD_REPOS_DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO non_mod_repos (repo_url, reason) VALUES (?, ?)", 
                 (repo_url, reason))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Repo already exists
        return False
    finally:
        conn.close()

def is_known_non_mod_repo(repo_url):
    """Check if a repo is known to not be a mod"""
    conn = sqlite3.connect(NON_MOD_REPOS_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM non_mod_repos WHERE repo_url=?", (repo_url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Enhanced Git work queue functions
def init_git_work_queue():
    """Initialize enhanced git work queue database"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS git_work_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            source TEXT,
            priority INTEGER DEFAULT 1,
            metadata TEXT,
            processed INTEGER DEFAULT 0,
            error TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_date TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_to_git_queue(url, source, priority=1, metadata=None):
    """Add a repository to the git work queue"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    try:
        metadata_str = json.dumps(metadata) if metadata else None
        c.execute("""
            INSERT INTO git_work_queue (url, source, priority, metadata) 
            VALUES (?, ?, ?, ?)
        """, (url, source, priority, metadata_str))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # URL already exists
    finally:
        conn.close()

def is_git_repo_in_queue(url):
    """Check if a git repository is already in the work queue"""
    conn = sqlite3.connect(GIT_QUEUE_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM git_work_queue WHERE url=?", (url,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_all_git_hosts(host_type=None):
    """Get all git hosts, optionally filtered by type"""
    conn = sqlite3.connect(GIT_HOSTS_DB)
    c = conn.cursor()
    if host_type:
        c.execute("SELECT host_url, host_type FROM git_hosts WHERE host_type=?", (host_type,))
    else:
        c.execute("SELECT host_url, host_type FROM git_hosts")
    results = c.fetchall()
    conn.close()
    return results

def add_mod_to_db(name, mod_type, author, description, source, url, metadata=None):
    """Add a discovered mod to the main database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Parse metadata if it's a JSON string
        if isinstance(metadata, str):
            try:
                metadata_dict = json.loads(metadata)
            except:
                metadata_dict = {}
        else:
            metadata_dict = metadata or {}
        
        # Insert the mod with all available information
        c.execute("""
            INSERT INTO results (
                name, type, author, description, source, repo_url,
                short_description, title, tags, depends, optional_depends,
                min_version, max_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            mod_type,
            author,
            description,
            source,
            url,
            metadata_dict.get('description', description),
            metadata_dict.get('title', name),
            json.dumps(metadata_dict.get('topics', [])),
            json.dumps(metadata_dict.get('depends', [])),
            json.dumps(metadata_dict.get('optional_depends', [])),
            metadata_dict.get('min_version', ''),
            metadata_dict.get('max_version', '')
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding mod to database: {e}")
        return False
    finally:
        conn.close()
