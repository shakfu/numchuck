#!/usr/bin/env bash
# Bash completion for numchuck CLI
# Install: source this file or copy to /etc/bash_completion.d/

_numchuck_completion() {
    local cur prev words cword
    _init_completion || return

    # Get current word being completed
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Top-level commands
    local commands="edit repl tui run version info"

    # If we're completing the first argument (command)
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi

    # Get the subcommand
    local subcommand="${COMP_WORDS[1]}"

    # Handle options based on previous word
    case "$prev" in
        --project)
            # Could list available projects from ~/.numchuck/projects/
            local projects_dir="$HOME/.numchuck/projects"
            if [ -d "$projects_dir" ]; then
                local projects=$(ls -1 "$projects_dir" 2>/dev/null)
                COMPREPLY=($(compgen -W "$projects" -- "$cur"))
            fi
            return 0
            ;;
        --srate)
            COMPREPLY=($(compgen -W "22050 44100 48000 96000" -- "$cur"))
            return 0
            ;;
        --channels)
            COMPREPLY=($(compgen -W "1 2" -- "$cur"))
            return 0
            ;;
        --duration)
            # No completion for duration (numeric)
            return 0
            ;;
    esac

    # Complete options based on subcommand
    case "$subcommand" in
        edit)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--project --start-audio" -- "$cur"))
            else
                # Complete .ck files
                COMPREPLY=($(compgen -f -X '!*.ck' -- "$cur"))
                # Add directories
                COMPREPLY+=($(compgen -d -- "$cur"))
            fi
            ;;
        repl|tui)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--start-audio --no-smart-enter --no-sidebar --project" -- "$cur"))
            else
                # Complete .ck files
                COMPREPLY=($(compgen -f -X '!*.ck' -- "$cur"))
                # Add directories
                COMPREPLY+=($(compgen -d -- "$cur"))
            fi
            ;;
        run)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--srate --channels --silent --duration" -- "$cur"))
            else
                # Complete .ck files
                COMPREPLY=($(compgen -f -X '!*.ck' -- "$cur"))
                # Add directories
                COMPREPLY+=($(compgen -d -- "$cur"))
            fi
            ;;
        version|info)
            # No options for these commands
            COMPREPLY=()
            ;;
        *)
            COMPREPLY=()
            ;;
    esac

    return 0
}

# Register completion function
complete -F _numchuck_completion numchuck
