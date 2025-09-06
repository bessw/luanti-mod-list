"""
Entry point for generating a modpack or game from a ContentDB collection URL.
"""
import sys
import os
import requests
import re
import shutil
from urllib.parse import urlparse
from contentdb.api import fetch_collection_data
from mod_type_detector import detect_repo_type


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m contentdb.collection_pack <collection_url> [output_dir]")
        sys.exit(1)
    collection_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        generate_from_collection(collection_url, output_dir)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)


def generate_from_collection(collection_url, output_dir=None):
    """
    Given a ContentDB collection URL, generate a modpack or game.
    If multiple games are present, raise an error.
    Also include extra mods from git links in the collection description.
    """
    # 1. Parse collection ID from URL
    parsed = urlparse(collection_url)
    match = re.search(r"/collections/(\d+)", parsed.path)
    if not match:
        raise ValueError("Invalid ContentDB collection URL")
    collection_id = match.group(1)

    # 2. Fetch collection data using contentdb.api
    data = fetch_collection_data(collection_id)

    mods = []
    games = []
    modpacks = []
    for entry in data.get("items", []):
        t = entry.get("type")
        if t == "mod":
            mods.append(entry)
        elif t == "game":
            games.append(entry)
        elif t == "modpack":
            modpacks.append(entry)

    # 3. Error if multiple games
    if len(games) > 1:
        raise RuntimeError("Collection contains multiple games. Cannot generate.")

    # 4. Parse description for extra git mod links
    desc = data.get("description", "")
    extra_git_mods = []
    # Improved: Look for a section like '# Additional Mods from git' and extract links
    extra_section = re.search(r"# Additional Mods from git[\s\S]*?(?:##|$)", desc)
    if extra_section:
        # Find all raw git links in the section and avoid duplicates
        extra_git_mods = list(set( re.findall(r"https?://[\w./-]+", extra_section.group(0)) ))

    # 5. Prepare output dir
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), f"collection_{collection_id}")
    os.makedirs(output_dir, exist_ok=True)

    # 6. Download/clone all mods, modpacks, games, and extra git mods
    all_items = []
    # Add ContentDB items
    for mod in mods:
        repo_url = mod.get("repo_url") or mod.get("url")
        mod_name = mod["name"]
        mod_dir = os.path.join(output_dir, mod_name)
        all_items.append((repo_url, mod_dir))
    for modpack in modpacks:
        repo_url = modpack.get("repo_url") or modpack.get("url")
        modpack_name = modpack["name"]
        modpack_dir = os.path.join(output_dir, modpack_name)
        all_items.append((repo_url, modpack_dir))
    for game in games:
        repo_url = game.get("repo_url") or game.get("url")
        game_name = game["name"]
        game_dir = os.path.join(output_dir, game_name)
        all_items.append((repo_url, game_dir))
    # Add extra git mods
    for git_url in extra_git_mods:
        mod_name = git_url.rstrip("/").split("/")[-1]
        mod_dir = os.path.join(output_dir, mod_name)
        all_items.append((git_url, mod_dir))
    # Clone all repos
    for repo_url, target_dir in all_items:
        if repo_url:
            os.system(f"git clone {repo_url} {target_dir}")
        else:
            os.makedirs(target_dir, exist_ok=True)

    # 7. Generate modpack.conf or game.conf
    if games:
        conf_path = os.path.join(output_dir, "game.conf")
        with open(conf_path, "w", encoding="utf-8") as f:
            f.write(f"name = {games[0]['name']}\ndescription = {games[0].get('description', '')}\n")
    else:
        conf_path = os.path.join(output_dir, "modpack.conf")
        with open(conf_path, "w", encoding="utf-8") as f:
            f.write(f"name = Collection {collection_id}\ndescription = {desc}\n")

    print(f"Generated at {output_dir}")


if __name__ == "__main__":
    main()
