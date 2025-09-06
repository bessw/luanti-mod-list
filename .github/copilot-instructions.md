# Copilot Instructions for Luanti Mod List System

## Project Overview
- **Purpose:** Discover and catalog Luanti (Minetest) mods, games, and modpacks from ContentDB, forums, and git repositories.
- **Architecture:** Modular Python system using a database for results and work queues. Major modules: contentdb, forum, git, and top-level queue/database utilities.

## Key Components
- `contentdb/`, `forum/`, `git/`: Source-specific modules for ContentDB, forum scraping, and git repo analysis.

## Developer Workflows
- **Testing:**
  - Run with `python -m unittest <test_file.py> -v` (see `tests/`)

## Patterns & Conventions
- **Mod/Game Detection:**
  - Look for `mod.conf` (mods), `game.conf` (games), or `modpack.conf` (modpacks) in repos.
  - Metadata extraction by parsing config files.
- **Error Handling:**
  - Network/API calls use timeouts and rate limiting.
  - Duplicate detection before queue insertion.
  - stop on errors

## Integration Points
- External dependencies: see `requirements.txt`
- Adding new git hosts: update `git_web.py`, add API integration and tests.

## File References
- ContentDB: `contentdb/`
- Forum: `forum/`
- Git: `git/`
- Tests: `tests/`

also consult the Readme.md file for further information