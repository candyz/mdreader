"""Shell completion script generator (Bash & Zsh) for mdreader CLI."""
from __future__ import annotations

BASH_COMPLETION_SCRIPT = r"""# bash completion for mdreader

_mdreader_completion() {
    local cur prev opts themes
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="-h --help -v --version -u --update -l --line -w --watch --width -t --theme --list-themes --toc --export-html --export-txt -s --syntax --inline --completion"
    themes="vim-dark github-dark github-light textual-dark textual-light tokyo-night monokai solarized-dark solarized-light catppuccin-frappe catppuccin-latte dracula nord"
    syntaxes="sh bash python c rust json html md markdown css js ts go yaml toml sql diff none"

    case "${prev}" in
        -t|--theme)
            COMPREPLY=( $(compgen -W "${themes}" -- "${cur}") )
            return 0
            ;;
        -s|--syntax)
            COMPREPLY=( $(compgen -W "${syntaxes}" -- "${cur}") )
            return 0
            ;;
        --completion)
            COMPREPLY=( $(compgen -W "bash zsh" -- "${cur}") )
            return 0
            ;;
        --export-html|--export-txt)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        -l|--line|--width)
            # Numeric arguments
            return 0
            ;;
    esac

    if [[ "${cur}" == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
        return 0
    else
        COMPREPLY=( $(compgen -f -- "${cur}") )
        return 0
    fi
}

complete -F _mdreader_completion mdreader
"""

ZSH_COMPLETION_SCRIPT = r"""#compdef mdreader

_mdreader() {
    local -a opts
    opts=(
        '(-h --help)'{-h,--help}'[Show help message and exit]'
        '(-v --version)'{-v,--version}'[Show version information and exit]'
        '(-u --update)'{-u,--update}'[Check for latest version and automatically update mdreader]'
        '(-l --line)'{-l,--line}'[Jump directly to line number on startup (1-indexed)]:line number:'
        '(-w --watch)'{-w,--watch}'[Watch mode: auto-reload when file changes on disk]'
        '--width[Cap content max width (in columns)]:columns:'
        '(-t --theme)'{-t,--theme}'[Set color theme]:theme:(vim-dark github-dark github-light textual-dark textual-light tokyo-night monokai solarized-dark solarized-light catppuccin-frappe catppuccin-latte dracula nord)'
        '--list-themes[List all available built-in color themes and exit]'
        '--toc[Show Table of Contents outline sidebar on startup]'
        '--export-html[Export document directly to standalone HTML file]:output file:_files'
        '--export-txt[Export document directly to plain text file]:output file:_files'
        '(-s --syntax)'{-s,--syntax}'[Override syntax highlighting language for plain/code files]:syntax:(sh bash python c rust json html md markdown css js ts go yaml toml sql diff none)'
        '--inline[Render Markdown directly to stdout without interactive TUI]'
        '--completion[Generate shell completion script (bash or zsh)]:shell:(bash zsh)'
        '*:file to preview:_files'
    )
    _arguments -s $opts
}

_mdreader "$@"
"""


def get_completion_script(shell: str = "bash") -> str:
    """Return completion script for the requested shell (bash or zsh)."""
    shell_lower = shell.lower().strip()
    if shell_lower == "zsh":
        return ZSH_COMPLETION_SCRIPT
    return BASH_COMPLETION_SCRIPT
