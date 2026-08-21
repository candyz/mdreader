# 🚀 mdreader Deployment & Installation Guide

[繁體中文版 (Traditional Chinese)](deployment_guide_zh-TW.md)

This guide provides instructions on installing and deploying **mdreader** (Terminal Markdown reader & Mermaid flowchart renderer) across **macOS** and **Linux** systems.

---

## 📋 System Requirements

| Requirement | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | macOS 12+ / Linux (Ubuntu, Debian, Arch, Rocky, RHEL, CentOS, etc.) | macOS (Apple Silicon / Intel) or Ubuntu 22.04+ / Rocky Linux 9+ |
| **Python Version** | Python 3.9+ | Python 3.10 ~ 3.14 |
| **Terminal** | UTF-8 / ANSI 256 Color Support | iTerm2, WezTerm, Ghostty, Alacritty, Kitty, or native Terminal |

---

## 🛠️ Method 1: Standard Installation via pipx (Recommended for Daily Use)

Using `pipx` installs CLI tools in completely isolated virtual environments while automatically adding the executable `mdreader` to your system `PATH`.

### 1. macOS Installation

```bash
# 1. Install pipx (if not already installed)
brew install pipx
pipx ensurepath

# 2. Clone repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# 3. Install via pipx
pipx install .

# 4. Verify installation
mdreader --version
```

### 2. Linux (Ubuntu / Debian) Installation

```bash
# 1. Update system and install python3, venv, pipx, and clipboard utilities
sudo apt update
sudo apt install -y python3 python3-pip python3-venv pipx xclip wl-clipboard
pipx ensurepath

# Apply PATH changes
source ~/.bashrc

# 2. Clone repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# 3. Install via pipx
pipx install .

# 4. Verify installation
mdreader --version
```

### 3. Linux (Arch Linux / Manjaro) Installation

```bash
sudo pacman -S python python-pip python-pipx xclip wl-clipboard
pipx ensurepath
source ~/.bashrc

git clone https://github.com/candyz/mdreader.git
cd mdreader
pipx install .
```

### 4. Linux (Rocky Linux / AlmaLinux / RHEL / CentOS Stream) Installation

```bash
# 1. Enable EPEL & CRB repositories (required for pipx and xclip)
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled crb   # Rocky 9+ / AlmaLinux 9+

# 2. Install Python 3, pip, pipx, and clipboard utilities
sudo dnf install -y python3 python3-pip pipx xclip wl-clipboard

pipx ensurepath
source ~/.bashrc

# 3. Clone repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# 4. Install via pipx
pipx install .

# 5. Verify installation
mdreader --version
```

---

## 💻 Method 2: Manual venv Deployment (Ideal for Development)

If the target system does not support `pipx`, use Python's built-in `venv` module:

```bash
# 1. Clone repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install project and dependencies in editable mode
pip install --upgrade pip
pip install -e .

# 5. (Optional) Create a global symlink in /usr/local/bin
sudo ln -sf $(pwd)/.venv/bin/mdreader /usr/local/bin/mdreader
```

---

## 📦 Method 3: Standalone Binary Packaging (PyInstaller)

For servers without a pre-existing Python environment, bundle `mdreader` into a standalone binary:

```bash
# 1. Install PyInstaller
source .venv/bin/activate
pip install pyinstaller

# 2. Build standalone executable
pyinstaller --onefile \
  --name mdreader \
  --collect-all textual \
  --collect-all rich \
  --collect-all termaid \
  src/mdreader/__main__.py

# 3. The compiled binary is located at dist/mdreader
./dist/mdreader --version

# 4. Distribute to target host
scp dist/mdreader user@remote-host:/usr/local/bin/
```

---

## 🔄 Upgrade & Uninstall

### Upgrading to the Latest Version
```bash
cd mdreader
git pull
pipx install . --force
```

### Uninstalling mdreader
```bash
pipx uninstall mdreader
```
