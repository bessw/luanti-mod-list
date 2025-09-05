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
    git = GitWeb.from_url(repo_url, branch)
    # Check for mod.conf
    mod_conf = git.get_file(MOD_CONF, branch=branch)
    if mod_conf:
        return RepoType.MOD, parse_mod_conf(mod_conf)
    # Check for modpack.conf
    modpack_conf = git.get_file(MODPACK_CONF, branch=branch)
    if modpack_conf:
        return RepoType.MODPACK, parse_modpack_conf(modpack_conf)
    # Check for game.conf
    game_conf = git.get_file(GAME_CONF, branch=branch)
    if game_conf:
        return RepoType.GAME, parse_game_conf(game_conf)
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
    metadata['type'] = RepoType.MOD
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
            elif key == 'description':
                metadata['description'] = value
            elif key == 'author':
                metadata['author'] = value
            elif key == 'title':
                metadata['title'] = value
    metadata['type'] = RepoType.MODPACK
    return metadata


def parse_game_conf(content):
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
    metadata['type'] = RepoType.GAME
    return metadata
