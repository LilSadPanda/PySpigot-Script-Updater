# PySpigot Script Updater

Keep your Minecraft server's PySpigot scripts always up-to-date — automatically or manually — by syncing directly from a GitHub repo (even private ones)! Designed with performance, safety, and flexibility in mind.

---

## 🎯 Features

- 🔁 Async GitHub script downloading (supports private repos)
- 🧠 SHA-based caching to skip unchanged scripts
- 🔐 Permission-based access (`script_updater.admin`)
- 💬 Color-coded, clean in-game reload summary
- 🧷 `/updatescripts force` support
- 📅 Auto-sync every X minutes via config
- ✅ Supports `script_targets: all` or specific scripts

---

## 🛠 Optimizations & Methods

- 🧵 Asynchronous file downloads to prevent main-thread lag
- ✅ Synchronous reloading handled safely via main-thread scheduling
- ✨ UTF-8 encoding and color handling via safe replacements (no `Â§` issues)
- ⚙️ Uses GitHub REST API with base64 decoding for reliable private/public repo access

---

## 📜 Commands

```
/updatescripts
/updatescripts force
```

- `force` reloads all scripts, ignoring hash cache
- Only accessible to users with permission

---

## 🧪 Tab Completion

```bash
/updatescripts [force]
```

---

## 🛡 Permissions

| Node                  | Description                            |
|-----------------------|----------------------------------------|
| `script_updater.admin` | Required to run `/updatescripts`      |

---

## 🧰 Configuration

After first run, a config file is generated:

📄 **Path:** `plugins/PySpigot/configs/script_updater_config.yml`

```yaml
github_repo_url: https://github.com/YourUser/YourRepo
private_repo: true
repo_sub_directory: scripts
github_pat_token: ghp_XXXXXXXXXXXXXXXXXXXX
local_directory: github
script_targets: all                # or: script1.py,script2.py
auto_sync_minutes: 10
```

### 🔄 `script_targets` Options:

- `all` — download and reload all `.py` scripts in the repo subdirectory
- `script1.py,script2.py` — only update specific scripts by name

---

## 📁 Example File Structure

### 🔗 GitHub Repo Example

```
MyRepo/
└── scripts/
    ├── example1.py
    ├── example2.py
    └── helper.py
```

Set `repo_sub_directory: scripts` to point at this folder.

---

### 📂 Local Server Structure

```
plugins/
└── PySpigot/
    ├── scripts/
    │   └── github/
    │       ├── example1.py
    │       ├── example2.py
    │       └── helper.py
    └── configs/
        ├── script_updater_config.yml
        └── .script_updater_hashes.json
```

`local_directory: github` puts synced files into `scripts/github/`.

---

## ✅ Installation

1. Place `script_updater.py` in your PySpigot `scripts/` folder
2. Restart the server or run:  
   ```bash
   /pyspigot reload script_updater.py
   ```
3. Edit the generated config file to match your GitHub repo
4. Use `/updatescripts` (or `force`) as needed
5. Set `auto_sync_minutes` to enable background auto-updates

---

Created by **LilSadPanda** with ❤️  
Feel free to fork or contribute!
