# -*- coding: utf-8 -*-
import pyspigot as ps
import os
import json
import base64
import hashlib
from java.net import URL
from java.io import BufferedReader, InputStreamReader, FileOutputStream
from dev.magicmq.pyspigot.manager.script import RunResult

logger = None
CONFIG_PATH = os.path.join("plugins", "PySpigot", "configs", "script_updater_config.yml")
HASHES_PATH = os.path.join("plugins", "PySpigot", "configs", ".script_updater_hashes.json")
DEFAULT_CONFIG = """# GitHub Script Updater Config
github_repo_url: https://github.com/YourUser/YourRepo
private_repo: true
repo_sub_directory: scripts
github_pat_token: ghp_REPLACE_ME
local_directory: github
script_targets: all
auto_sync_minutes: 10
"""

GITHUB_TOKEN = ""
SCRIPT_FOLDER = ""
API_FOLDER_URL = ""
SCRIPT_TARGETS = "all"
COLOR_CHAR = unichr(167)  # Safe way to insert "§"

def start(script):
    global logger, GITHUB_TOKEN, SCRIPT_FOLDER, API_FOLDER_URL, SCRIPT_TARGETS

    logger = script.getLogger()
    ensure_config_exists()

    config = load_config()

    github_url = config["github_repo_url"]
    repo_parts = github_url.strip("/").split("/")
    if len(repo_parts) < 5:
        logger.severe("Invalid GitHub repo URL in config.")
        return

    owner = repo_parts[-2]
    repo = repo_parts[-1]
    subdir = config.get("repo_sub_directory", "scripts")
    GITHUB_TOKEN = config.get("github_pat_token", "")
    local_dir = config.get("local_directory", "github")
    SCRIPT_TARGETS = config.get("script_targets", "all").replace(" ", "").lower()

    API_FOLDER_URL = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repo, subdir)
    SCRIPT_FOLDER = os.path.join("plugins", "PySpigot", "scripts", local_dir)

    logger.info("Loaded config from: {}".format(CONFIG_PATH))

    interval = int(config.get("auto_sync_minutes", "0"))
    if interval > 0:
        ticks = interval * 60 * 20
        ps.scheduler.scheduleAsyncRepeatingTask(sync_and_schedule_reload, 0, ticks, API_FOLDER_URL, SCRIPT_FOLDER, False, None)

    ps.commands.registerCommand(script_updater_command, script_updater_tab, "updatescripts")

def ensure_config_exists():
    if not os.path.exists(os.path.dirname(CONFIG_PATH)):
        os.makedirs(os.path.dirname(CONFIG_PATH))
    if not os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            f.write(DEFAULT_CONFIG)
        print("[script_updater] Created default config.")
    if not os.path.isfile(HASHES_PATH):
        with open(HASHES_PATH, "w") as f:
            json.dump({}, f)

def load_config():
    config = {}
    with open(CONFIG_PATH, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                config[key] = val
    return config

def sha256(content):
    return hashlib.sha256(content).hexdigest()

def load_hashes():
    if not os.path.exists(HASHES_PATH):
        return {}
    with open(HASHES_PATH, "r") as f:
        return json.load(f)

def save_hashes(hashes):
    with open(HASHES_PATH, "w") as f:
        json.dump(hashes, f)

def read_json_from_url(api_url):
    url = URL(api_url)
    connection = url.openConnection()
    if GITHUB_TOKEN:
        connection.setRequestProperty("Authorization", "token " + GITHUB_TOKEN)
    connection.setRequestProperty("Accept", "application/vnd.github.v3+json")
    connection.connect()
    if connection.getResponseCode() != 200:
        return None
    reader = BufferedReader(InputStreamReader(connection.getInputStream()))
    content = ""
    line = reader.readLine()
    while line:
        content += line
        line = reader.readLine()
    reader.close()
    return json.loads(content)

def sync_and_schedule_reload(api_folder_url, local_dir, force, sender):
    files = read_json_from_url(api_folder_url)
    if files is None:
        if sender:
            sender.sendMessage(COLOR_CHAR + "cGitHub API error - failed to fetch scripts.")
        return

    existing_hashes = load_hashes()
    updated_hashes = existing_hashes.copy()

    to_reload = []
    downloaded = []
    unchanged = []
    failed = []

    for entry in files:
        name = entry["name"]
        if not name.endswith(".py"):
            continue
        if SCRIPT_TARGETS != "all" and name.lower() not in SCRIPT_TARGETS.split(","):
            continue

        json_data = read_json_from_url(entry["url"])
        if not json_data or "content" not in json_data:
            failed.append(name)
            continue

        raw_content = base64.b64decode(json_data["content"])
        content_hash = sha256(raw_content)

        if not force and name in existing_hashes and existing_hashes[name] == content_hash:
            unchanged.append(name)
            continue

        local_path = os.path.join(local_dir, name)
        with open(local_path, "wb") as f:
            f.write(raw_content)
        updated_hashes[name] = content_hash
        downloaded.append(name)
        to_reload.append(name)

    save_hashes(updated_hashes)
    ps.scheduler.runTask(perform_reload, to_reload, downloaded, unchanged, failed, sender)

def perform_reload(to_reload, downloaded, unchanged, failed, sender):
    reloaded = []

    for name in to_reload:
        if ps.script.isScriptRunning(name):
            ps.script.unloadScript(name)
        result = ps.script.loadScript(name)
        if result == RunResult.SUCCESS:
            reloaded.append(name)
        else:
            failed.append(name)

    messages = [
        "&7&m----------------------------",
        "&aScript Updater Summary:",
        "&7Downloaded: &f{}".format(", ".join(downloaded) if downloaded else "None"),
        "&7Reloaded: &f{}".format(", ".join(reloaded) if reloaded else "None"),
        "&7Unchanged: &f{}".format(", ".join(unchanged) if unchanged else "None"),
        "&7Failed: &c{}".format(", ".join(failed) if failed else "None"),
        "&7&m----------------------------"
    ]
    if sender:
        for msg in messages:
            sender.sendMessage(msg.replace("&", COLOR_CHAR))

def script_updater_command(sender, label, args):
    if not sender.hasPermission("script_updater.admin"):
        sender.sendMessage(COLOR_CHAR + "cYou do not have permission to use this command.")
        return True

    force = False
    if args and args[0].lower() == "force":
        force = True

    ps.scheduler.runTaskAsync(sync_and_schedule_reload, API_FOLDER_URL, SCRIPT_FOLDER, force, sender)
    return True

def script_updater_tab(sender, label, args):
    if not sender.hasPermission("script_updater.admin"):
        return []
    if len(args) == 1:
        return ["force"]
    return []
