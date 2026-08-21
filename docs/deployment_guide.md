# 🚀 mdreader 部署與安裝手冊 (Deployment & Installation Guide)

本手冊說明如何將 **mdreader**（終端 Markdown 預覽與 Mermaid 流程圖閱讀器）安裝與部署到其他台電腦（支援 **macOS** 與 **Linux**）。

---

## 📋 系統環境需求

| 項目 | 最低需求 | 推薦環境 |
| :--- | :--- | :--- |
| **作業系統** | macOS 12+ / Linux (Ubuntu, Debian, Arch, Rocky, RHEL, CentOS 等) | macOS (Apple Silicon / Intel) 或 Ubuntu 22.04+ / Rocky Linux 9+ |
| **Python 版本** | Python 3.9+ | Python 3.10 ~ 3.14 |
| **終端環境** | 支援 UTF-8 / ANSI 256 色 | iTerm2, WezTerm, Ghostty, Alacritty, Kitty 或標準 Terminal |

---

## 🛠️ 方式一：標準推薦安裝（pipx 獨立環境隔離，推薦日常使用）

使用 `pipx` 可以將 CLI 工具安裝在完全隔離的虛擬環境中，且自動將可執行檔 `mdreader` 加入系統全域 `PATH`，無須手動啟動虛擬環境。

### 1. macOS 安裝步驟

```bash
# 1. 安裝 pipx（若尚未安裝）
brew install pipx
pipx ensurepath

# 2. 複製專案庫 (或從遠端 Git 下載)
git clone https://github.com/candyz0416/mdreader.git
cd mdreader

# 3. 使用 pipx 進行本地安裝
pipx install .

# 4. 驗證安裝成功
mdreader --version
```

### 2. Linux (Ubuntu / Debian) 安裝步驟

```bash
# 1. 更新系統並安裝 python3, venv, pipx 及剪貼簿工具 (xclip / wl-clipboard)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv pipx xclip wl-clipboard
pipx ensurepath

# 套用 PATH 變更
source ~/.bashrc

# 2. 複製專案
git clone https://github.com/candyz0416/mdreader.git
cd mdreader

# 3. 透過 pipx 部署安裝
pipx install .

# 4. 驗證安裝成功
mdreader --version
```

### 3. Linux (Arch Linux / Manjaro) 安裝步驟

```bash
sudo pacman -S python python-pip python-pipx xclip wl-clipboard
pipx ensurepath
source ~/.bashrc

git clone https://github.com/candyz0416/mdreader.git
cd mdreader
pipx install .
```

### 4. Linux (Rocky Linux / AlmaLinux / RHEL / CentOS Stream) 安裝步驟

```bash
# 1. 啟用 EPEL 與 CRB 套件庫（提供 pipx 與 xclip 等工具）
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled crb   # Rocky 9+ / AlmaLinux 9+

# 2. 安裝 Python 3, pip, pipx 及剪貼簿工具
sudo dnf install -y python3 python3-pip pipx xclip wl-clipboard

# 若系統預設 Python 版本低於 3.9，可安裝較新版本：
# sudo dnf install -y python3.11 python3.11-pip
# 並使用 python3.11 -m pipx 替代 pipx 指令

pipx ensurepath
source ~/.bashrc

# 3. 複製專案
git clone https://github.com/candyz0416/mdreader.git
cd mdreader

# 4. 透過 pipx 部署安裝
pipx install .

# 5. 驗證安裝成功
mdreader --version
```

---

## 💻 方式二：手動 venv 虛擬環境部署（適合開發與測試）

若目標電腦不支援 pipx，可使用 Python 內建的 `venv` 模組：

```bash
# 1. 下載專案代碼
git clone https://github.com/candyz0416/mdreader.git
cd mdreader

# 2. 建立虛擬環境
python3 -m venv .venv

# 3. 啟動虛擬環境
source .venv/bin/activate

# 4. 安裝專案與依賴
pip install --upgrade pip
pip install -e .

# 5. (可選) 建立全域捷徑 Symlink 到 /usr/local/bin
sudo ln -sf $(pwd)/.venv/bin/mdreader /usr/local/bin/mdreader
```

---

## 📦 方式三：打包為獨立二進制檔案 (Standalone Binary)

若目標伺服器未安裝 Python 環境，可以在構建機上透過 `PyInstaller` 封裝成單一可執行檔：

```bash
# 1. 安裝 PyInstaller
source .venv/bin/activate
pip install pyinstaller

# 2. 打包為單一二進制可執行檔
pyinstaller --onefile \
  --name mdreader \
  --collect-all textual \
  --collect-all rich \
  --collect-all termaid \
  src/mdreader/__main__.py

# 3. 產生的可執行檔位於 dist/mdreader
./dist/mdreader --version

# 4. 分發到目標機器：直接將 dist/mdreader 複製到目標主機 /usr/local/bin/ 即可直接執行
scp dist/mdreader user@remote-host:/usr/local/bin/
```

---

## 🔄 升級與移除 (Upgrade & Uninstall)

### 升級最新版本
```bash
cd mdreader
git pull
pipx install . --force
```

### 移除 mdreader
```bash
pipx uninstall mdreader
```
