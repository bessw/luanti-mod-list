from git.git_web import GitWeb

MOD_CONF = 'mod.conf'
MODPACK_CONF = 'modpack.conf'
GAME_CONF = 'game.conf'

class RepoType:
    MOD = 'mod'
    MODPACK = 'modpack'
    GAME = 'game'
    UNKNOWN = 'unknown'


def detect_repo_type(repo_url, branch=None):
    """
    Detect if a repository is a Luanti mod, modpack, or game using the GitWeb abstraction.
    Returns: (repo_type, metadata)
    """
    try:
        if not GitWeb.is_git_server(repo_url):
            return RepoType.UNKNOWN, {}
        git = GitWeb.from_url(repo_url, branch)
    except Exception as e:
        print(f"[DEBUG] GitWeb.from_url failed: {e}")
        return RepoType.UNKNOWN, {}
    # Check for game.conf first (games may also have mod.conf)
    try:
        game_conf = git.get_file(GAME_CONF, branch=branch)
        print(f"[DEBUG] game.conf: {bool(game_conf)}")
        if game_conf:
            return RepoType.GAME, parse_game_conf(game_conf)
    except Exception as e:
        print(f"[DEBUG] game.conf fetch failed: {e}")
    try:
        modpack_conf = git.get_file(MODPACK_CONF, branch=branch)
        print(f"[DEBUG] modpack.conf: {bool(modpack_conf)}")
        if modpack_conf:
            return RepoType.MODPACK, parse_modpack_conf(modpack_conf)
    except Exception as e:
        print(f"[DEBUG] modpack.conf fetch failed: {e}")
    try:
        mod_conf = git.get_file(MOD_CONF, branch=branch)
        print(f"[DEBUG] mod.conf: {bool(mod_conf)}")
        if mod_conf:
            return RepoType.MOD, parse_mod_conf(mod_conf)
    except Exception as e:
        print(f"[DEBUG] mod.conf fetch failed: {e}")
    return RepoType.UNKNOWN, {}


def parse_mod_conf(content):
    metadata = {}
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == 'name':
                metadata['name'] = value
            elif key == 'title':
                metadata['title'] = value
            elif key == 'description':
                metadata['description'] = value
            elif key == 'depends':
                metadata['depends'] = [dep.strip() for dep in value.split(',') if dep.strip()]
            elif key == 'optional_depends':
                metadata['optional_depends'] = [dep.strip() for dep in value.split(',') if dep.strip()]
            elif key == 'author':
                metadata['author'] = value
            elif key == 'min_minetest_version' or key == 'min_luanti_version':
                metadata['min_version'] = value
            elif key == 'max_minetest_version' or key == 'max_luanti_version':
                metadata['max_version'] = value
    # API logic: fallback for missing values
    metadata['type'] = RepoType.MOD
    metadata['title'] = metadata.get('title', metadata.get('name', ''))
    metadata['name'] = metadata.get('name', metadata.get('title', ''))
    metadata['description'] = metadata.get('description', '')
    return metadata


def parse_modpack_conf(content):
    metadata = {}
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == 'name':
                metadata['name'] = value
            elif key == 'title':
                metadata['title'] = value
            elif key == 'description':
                metadata['description'] = value
            elif key == 'author':
                metadata['author'] = value
    # API logic: fallback for missing values
    metadata['type'] = RepoType.MODPACK
    metadata['title'] = metadata.get('title', metadata.get('name', ''))
    metadata['name'] = metadata.get('name', metadata.get('title', ''))
    metadata['description'] = metadata.get('description', '')
    return metadata


def parse_game_conf(content):
    metadata = {}
    for line in content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == 'title':
                metadata['title'] = value
            elif key == 'name':
                metadata['name'] = value
            elif key == 'description':
                metadata['description'] = value
            elif key == 'author':
                metadata['author'] = value
    # API logic: fallback for missing values
    metadata['type'] = RepoType.GAME
    metadata['title'] = metadata.get('title', metadata.get('name', ''))
    metadata['name'] = metadata.get('name', metadata.get('title', ''))
    metadata['description'] = metadata.get('description', '')
    return metadata
