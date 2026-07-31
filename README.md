# Monkeypatched devcontainer setup from Anthropic

- Source: [Claude Code GitHub](https://github.com/anthropics/claude-code/tree/main)

Setup proxy on Docker and IDE and start container

Extended version for .NET by [Andreas Baranow](https://github.com/evandrii)

---
## Description

A pre-configured, network-restricted Docker container for running the [Claude Code](https://github.com/anthropics/claude-code) CLI. 
Your project stays on your host machine; only a bind-mounted copy is exposed inside the container, so an agent's shell commands and file access stay isolated from the rest of your machine.

## What's in here

| File | Purpose |
|---|---|
| `.devcontainer/Dockerfile` | Node 20 image with git, zsh, gh, iptables/ipset, the **.NET SDK** (build arg `DOTNET_VERSION`, default `8.0`) and `@anthropic-ai/claude-code` installed globally — preconfigured for .NET development. |
| `.devcontainer/devcontainer.json` | Editor-agnostic container spec (used by VS Code's Dev Containers extension, and readable by other devcontainer-CLI tooling). |
| `.devcontainer/init-firewall.sh` | Restricts the container's outbound network to an allowlist (Anthropic API, npm, GitHub, etc.). |
| `.claude/skills/` | Custom Claude Code skills bundled with this repo (e.g. `grill-me`). |
| `CLAUDE.md` | Project-specific instructions read automatically by Claude Code. |

> **Known issue:** `init-firewall.sh` is currently an empty file. The container will build and run, but the network allowlist it's supposed to set up does **not** take effect yet. Restore it from [upstream](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh) before relying on the network isolation.

## Prerequisites

- **Windows 10/11** with **WSL2** enabled.
- **Docker Desktop**, configured to use the **WSL2 backend**, running.
- A way to authenticate Claude Code — see [Authentication](#authentication) below for the three supported options.
- *(Optional, for the VS Code workflow)* VS Code + the **Dev Containers** extension (`ms-vscode-remote.remote-containers`).

Verify Docker is healthy before continuing:

```powershell
docker version
wsl -l -v
```

## Authentication

The container ships with `@anthropic-ai/claude-code` installed, but not credentials. Pick whichever of these three fits how you work:

### 1. Log in with your Claude.ai / Anthropic Console account

No host setup required. Once you have a shell inside the container, just run:

```bash
claude
```

and follow the interactive login flow. Credentials are cached in the `claude-code-config` volume (mounted at `/home/node/.claude`), so you won't be asked again on the next `docker start` / container reopen — only after a full rebuild.

### 2. Export an API key manually, per session

Good for a quick one-off test, or trying a key that isn't meant to be persistent. Inside the container shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# optional, if you're routing through a gateway instead of api.anthropic.com:
export ANTHROPIC_BASE_URL=https://ai-gateway.company.com

claude
```

This only lasts for the current shell session — you'll re-export it every time you start a new one.

### 3. Bake the key in via persistent Windows environment variables (recommended for repeat use)

`devcontainer.json`'s `containerEnv` maps two host-side variables into the container automatically on every build, so you never type the key in again:

```jsonc
"containerEnv": {
  "ANTHROPIC_BASE_URL": "${localEnv:ANTHROPIC_BASE_URL_DEVCONTAINER}",
  "ANTHROPIC_AUTH_TOKEN": "${localEnv:ANTHROPIC_AUTH_TOKEN_DEVCONTAINER}"
}
```

Set those up once on the Windows host:

1. **Set persistent Windows *user* environment variables.** Run this yourself in a PowerShell prompt — `ANTHROPIC_AUTH_TOKEN_DEVCONTAINER` is a secret, so don't paste the real value into chat with an assistant:

   ```powershell
   [Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL_DEVCONTAINER", "https://ai-gateway.company.com", "User")
   [Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN_DEVCONTAINER", "sk-xxxxxxxxxxxxxxxxxxx", "User")
   ```

   (Equivalent to setting them via System Properties → Environment Variables in the GUI.)

2. **Fully quit VS Code** — every window, from the tray/taskbar, not just "Reload Window." VS Code inherits its environment once, at process launch, from whatever shell/session started it; a variable set after VS Code is already running won't be visible to it until VS Code itself restarts as a new process.

3. **Relaunch VS Code**, then run **"Dev Containers: Rebuild Container"** (not just reopen). `containerEnv` values are resolved and baked in at build time, so a container that's merely restarted or reopened — without a rebuild — won't pick up a newly-set host variable either.

> This mechanism is specific to `devcontainer.json` (Option B below). If you're using plain Docker (Option A), pass the equivalent `-e` flags yourself, e.g. `-e ANTHROPIC_AUTH_TOKEN=$env:ANTHROPIC_AUTH_TOKEN_DEVCONTAINER`.

## Option A — Plain Docker (no IDE required)

This works from any terminal (PowerShell, Windows Terminal, or a terminal inside Visual Studio / VS Code) and mirrors what the Dev Containers extension does under the hood.

1. **Build the image:**

   ```powershell
   cd .devcontainer
   docker build -t claude-sandbox `
     --build-arg CLAUDE_CODE_VERSION=latest `
     --build-arg GIT_DELTA_VERSION=0.18.2 `
     --build-arg ZSH_IN_DOCKER_VERSION=1.2.0 `
     --build-arg DOTNET_VERSION=8.0 `
     .
   cd ..
   ```

2. **Run the container**, bind-mounting the repo root to `/workspace` and granting the network capabilities the firewall script needs:

   ```powershell
   docker run -it `
     --cap-add=NET_ADMIN --cap-add=NET_RAW `
     -v "${PWD}:/workspace" `
     -v claude-code-config:/home/node/.claude `
     -v claude-code-bashhistory:/commandhistory `
     -e NODE_OPTIONS=--max-old-space-size=4096 `
     -e CLAUDE_CONFIG_DIR=/home/node/.claude `
     claude-sandbox zsh
   ```

3. **(Optional) apply the firewall**, as root, once inside the container shell:

   ```bash
   sudo /usr/local/bin/init-firewall.sh
   ```

   (No-ops until the script is restored — see the known issue above.)

4. **Authenticate and start Claude Code** — see [Samples](#samples-using-claude-code-inside-the-container) below.

To come back to the same container later instead of rebuilding:

```powershell
docker start -ai <container_id_or_name>
```

## Option B — VS Code + Dev Containers extension

1. Install the **Dev Containers** extension in VS Code.
2. Open this folder in VS Code.
3. `Ctrl+Shift+P` → **"Dev Containers: Reopen in Container"**.
4. VS Code builds the image, mounts the repo at `/workspace`, and runs `init-firewall.sh` automatically as the `postStartCommand`. The integrated terminal now runs inside the container.

## Option C — Visual Studio (2022/2026)

Visual Studio (the full IDE, distinct from VS Code) does **not** read `.devcontainer/devcontainer.json` — its container tooling targets Docker Compose–based .NET projects and won't pick this setup up automatically. If you want to keep editing in Visual Studio while running the agent sandboxed, the practical approach is:

1. Keep editing files in Visual Studio as normal — it's just editing files on disk in this repo.
2. Get the container running once, either via **Option A** (`docker build` + `docker run`) or by opening the folder in VS Code once for **Option B**. Either way, leave it running (or `docker start` it again) rather than rebuilding it every time.
3. Open a terminal *inside Visual Studio itself* and attach a shell to that already-running container:

   - **Tools → Command Line → Terminal**
   - Find the container's name (Docker assigns a random one, e.g. `priceless_gould`, unless you passed `--name`):

     ```powershell
     docker ps
     ```
   - Attach a shell to it:

     ```powershell
     docker exec -it priceless_gould bash
     ```
   - Then start Claude Code as usual:

     ```bash
     claude
     ```
4. Because `/workspace` is bind-mounted to this repo, changes Claude Code makes inside the container appear immediately in Visual Studio, and vice versa.

In short: Visual Studio and the container are decoupled — VS is only editing the host files, the container is a separate sandboxed shell you `docker exec` into rather than one Visual Studio builds or manages itself.

> `docker exec` opens an *additional* shell into a container that's already running — it doesn't start one. If `docker ps` comes up empty, there's nothing to exec into yet; go back to step 2.


## Using the sandbox with an existing project

Everything above assumes you're working inside this repo. To sandbox a project that already lives elsewhere — say `D:\dev\source\project1` — you have two options.

### Option 1 — Copy the sandbox files into the project (recommended)

Makes the project self-contained: anyone who clones `project1` gets the same sandbox, with no ongoing dependency on this repo.

1. Copy `.devcontainer/` into the project (and, if you want the same custom skills/instructions too, `.claude/` and `CLAUDE.md`):

   ```powershell
   Copy-Item -Recurse "D:\dev\source\COMPANY\ai-sandbox\.devcontainer" "D:\dev\source\project1\.devcontainer"
   Copy-Item -Recurse "D:\dev\source\COMPANY\ai-sandbox\.claude" "D:\dev\source\project1\.claude"
   Copy-Item "D:\dev\source\COMPANY\ai-sandbox\CLAUDE.md" "D:\dev\source\project1\CLAUDE.md"
   ```

2. Open `D:\dev\source\project1` in VS Code.
3. `Ctrl+Shift+P` → **"Dev Containers: Reopen in Container"** — same as Option B, but now building from `project1`'s own copy of the config.

No path editing needed: `workspaceMount` uses `${localWorkspaceFolder}`, so it automatically binds whichever folder VS Code has open. Commit `.devcontainer/` (and friends) into `project1`'s own repo so the sandbox travels with the project from then on.

> Each project gets its own `claude-code-config` / `claude-code-bashhistory` volumes — devcontainer.json suffixes them with `${devcontainerId}`, derived from the container config, so logging in / shell history in `project1`'s container is isolated from this repo's.

### Option 2 — Mount the project into this repo's container, without copying anything

Keeps one canonical copy of the Dockerfile/devcontainer.json here, and reuses the same built image across as many external projects as you like. This is just **Option A** with the bind mount pointed at `project1` instead of `${PWD}`:

```powershell
cd D:\dev\source\EVIA\ai-sandbox\.devcontainer
docker build -t claude-sandbox `
  --build-arg CLAUDE_CODE_VERSION=latest `
  --build-arg GIT_DELTA_VERSION=0.18.2 `
  --build-arg ZSH_IN_DOCKER_VERSION=1.2.0 `
  --build-arg DOTNET_VERSION=8.0 `
  .
cd ..

docker run -it `
  --cap-add=NET_ADMIN --cap-add=NET_RAW `
  -v "D:/dev/source/project1:/workspace" `
  -v claude-code-config:/home/node/.claude `
  -v claude-code-bashhistory:/commandhistory `
  -e NODE_OPTIONS=--max-old-space-size=4096 `
  -e CLAUDE_CONFIG_DIR=/home/node/.claude `
  claude-sandbox zsh
```

The only change from Option A is `-v "D:/dev/source/project1:/workspace"` in place of `-v "${PWD}:/workspace"`. Once inside, `/workspace` *is* `project1` — keep editing it from Visual Studio or VS Code on the host as usual (see **Option C** for attaching a terminal to an already-running container from Visual Studio).

> Unlike Option 1, these named volumes aren't project-scoped — every project you sandbox this way shares one Claude Code login and shell history. Usually that's what you want (you only authenticate once per machine), but it does mean the projects aren't isolated from each other's command history the way Option 1's per-project volumes are.

## Samples: using Claude Code inside the container

Once you have a shell inside the container (from any of the options above) and you're authenticated (see [Authentication](#authentication)), you're at `/workspace`:

```bash
# Interactive session
claude

# One-shot / scriptable ("print mode")
claude -p "List the top-level files in this repo and summarize what each does"

# Use a bundled custom skill from .claude/skills/
claude
> /grill-me I'm thinking of rewriting our auth middleware, poke holes in the plan

# .NET is preinstalled — sanity check the SDK
dotnet --version
```

## Troubleshooting

**Changed the Dockerfile, devcontainer.json, or a host env var and nothing happened**

This is a container — it's built once from those files, then reused. Editing them on disk doesn't touch the running (or stopped) container; you have to make it rebuild:

- **VS Code (Option B):** `Ctrl+Shift+P` → **"Dev Containers: Rebuild Container"**. "Reopen in Container" or a plain window reload reuses the existing image and will *not* pick up your edit. If the rebuild itself looks stale (e.g. an `apt-get`/`npm install` layer didn't actually change), use **"Dev Containers: Rebuild Without Cache"** instead.
- **Plain Docker (Option A):** re-run the `docker build` command — it re-reads the Dockerfile and only invalidates the layers that changed. Force a fully clean build with `docker build --no-cache ...` if you suspect a stale cached layer.
- **Host environment variables** (e.g. the `ANTHROPIC_*_DEVCONTAINER` vars from [Authentication](#authentication)) are resolved into `containerEnv` at build time, not read live — the same rebuild is required, and VS Code itself needs a full restart first if it was already running when you changed them.

If a rebuild still doesn't fix it, the old container/image may be lingering and getting reused instead of the new one:

```powershell
# see what's actually there
docker ps -a
docker images

# remove a specific stale container / image once you've identified it
docker rm <container_id_or_name>
docker image rm claude-sandbox

# nuclear option: reclaim disk space from everything Docker isn't currently using
# (stopped containers, dangling images, unused networks — NOT named volumes)
docker system prune
```

`docker system prune` does **not** touch the named volumes (`claude-code-config`, `claude-code-bashhistory`), so your Claude Code login and shell history survive it. If you deliberately want to reset those too (e.g. to force a fresh `claude` login):

```powershell
docker volume rm claude-code-config claude-code-bashhistory
```

Both of the commands above are destructive and irreversible — double-check `docker ps -a` / `docker volume ls` for anything you still need before running them.

**`docker: Error response from daemon: accessing specified distro mount service: stat /run/guest-services/distro-services/<distro>.sock: no such file or directory`**

This is a Docker Desktop ↔ WSL2 integration glitch, unrelated to this repo's Dockerfile (the image build itself succeeds). Docker Desktop has lost track of the guest-services socket for your WSL distro. Fixes, roughly in order of least to most disruptive:

1. Quit Docker Desktop completely (system tray → Quit) and restart it.
2. In a terminal: `wsl --shutdown`, then restart Docker Desktop.
3. Docker Desktop → **Settings → Resources → WSL Integration** — confirm the distro shown in `wsl -l -v` is toggled on.
4. `wsl --update`, then restart Windows if the problem persists.
