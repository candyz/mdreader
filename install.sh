#!/usr/bin/env bash
# ==============================================================================
# mdreader installer script
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/candyz/mdreader/main/install.sh | bash
# ==============================================================================
set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

REPO_URL="git+https://github.com/candyz/mdreader.git"

print_banner() {
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
               _                    _           
  _ __ ___   __| |_ __ ___  __ _  __| | ___ _ __ 
 | '_ ` _ \ / _` | '__/ _ \/ _` |/ _` |/ _ \ '__|
 | | | | | | (_| | | |  __/ (_| | (_| |  __/ |   
 |_| |_| |_|\__,_|_|  \___|\__,_|\__,_|\___|_|   
EOF
    echo -e "${NC}"
    echo -e "${BOLD}Markdown Reader TUI - Terminal Markdown Viewer with Style${NC}"
    echo ""
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check Python 3 version >= 3.9
check_python() {
    if ! command -v python3 &>/dev/null; then
        error "Python 3 is not installed. Please install Python 3.9 or newer."
        exit 1
    fi

    local py_ver
    py_ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    local major
    major="$(echo "$py_ver" | cut -d. -f1)"
    local minor
    minor="$(echo "$py_ver" | cut -d. -f2)"

    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 9 ]; }; then
        error "Python version $py_ver is too old. mdreader requires Python 3.9+."
        exit 1
    fi
    success "Python $py_ver detected."
}

# Check Git
check_git() {
    if ! command -v git &>/dev/null; then
        error "git is not installed. Please install git."
        exit 1
    fi
    success "Git detected."
}

# Install via pipx or uv
install_mdreader() {
    if command -v pipx &>/dev/null; then
        info "Installing mdreader using pipx..."
        pipx install "${REPO_URL}" --force
        return 0
    fi

    if command -v uv &>/dev/null; then
        info "Installing mdreader using uv tool..."
        uv tool install --force --reinstall "${REPO_URL}"
        return 0
    fi

    # If neither is available, attempt to install uv or pipx
    info "Neither pipx nor uv is installed. Checking alternatives..."
    if command -v curl &>/dev/null; then
        info "Installing uv (fast Python package and tool manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Load uv into current PATH for remainder of script
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        if command -v uv &>/dev/null; then
            info "Installing mdreader using uv tool..."
            uv tool install --force --reinstall "${REPO_URL}"
            return 0
        fi
    fi

    # Fallback: standard user pip install
    info "Attempting fallback installation via 'python3 -m pip install --user'..."
    python3 -m pip install --user --upgrade "${REPO_URL}"
}

verify_installation() {
    export PATH="$HOME/.local/bin:$PATH"

    if command -v mdreader &>/dev/null; then
        local installed_version
        installed_version="$(mdreader --version 2>&1 || true)"
        echo ""
        success "${BOLD}mdreader successfully installed! ($installed_version)${NC}"
    else
        warn "Installation completed, but 'mdreader' was not found in your current PATH."
    fi

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        warn "~/.local/bin is not in your PATH."
        info "Add the following line to your shell configuration (~/.bashrc, ~/.zshrc, etc.):"
        echo -e "${CYAN}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi

    echo ""
    echo -e "${BOLD}Get started:${NC}"
    echo -e "  Run: ${CYAN}mdreader <file.md>${NC}"
    echo -e "  Update anytime: ${CYAN}mdreader -u${NC}"
    echo -e "  Help: ${CYAN}mdreader --help${NC}"
    echo ""
}

main() {
    print_banner
    check_python
    check_git
    install_mdreader
    verify_installation
}

main "$@"
