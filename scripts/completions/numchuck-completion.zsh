#compdef numchuck
# Zsh completion for numchuck CLI
# Install: Copy to a directory in $fpath (e.g., /usr/local/share/zsh/site-functions/_numchuck)

_numchuck() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \
        '1: :->command' \
        '*::arg:->args'

    case $state in
        command)
            local -a commands
            commands=(
                'edit:Launch multi-tab editor for livecoding'
                'repl:Launch interactive REPL'
                'tui:Launch interactive REPL (alias for repl)'
                'run:Execute ChucK files from command line'
                'version:Show version information'
                'info:Show ChucK and numchuck info'
            )
            _describe 'numchuck command' commands
            ;;
        args)
            case $line[1] in
                edit)
                    _arguments \
                        '*:ChucK files:_files -g "*.ck"' \
                        '--project[Project name for versioned file storage]:project:_numchuck_projects' \
                        '--start-audio[Start audio automatically on startup]'
                    ;;
                repl|tui)
                    _arguments \
                        '*:ChucK files:_files -g "*.ck"' \
                        '--start-audio[Start audio automatically on REPL startup]' \
                        '--no-smart-enter[Disable smart Enter mode]' \
                        '--no-sidebar[Hide topbar showing active shreds]' \
                        '--project[Project name for versioned file storage]:project:_numchuck_projects'
                    ;;
                run)
                    _arguments \
                        '*:ChucK files:_files -g "*.ck"' \
                        '--srate[Sample rate]:sample rate:(22050 44100 48000 96000)' \
                        '--channels[Number of audio channels]:channels:(1 2)' \
                        '--silent[Run without audio output]' \
                        '--duration[Run for specified duration in seconds]:duration (seconds):'
                    ;;
                version|info)
                    # No arguments
                    ;;
            esac
            ;;
    esac
}

# Helper function to list available projects
_numchuck_projects() {
    local projects_dir="$HOME/.numchuck/projects"
    if [ -d "$projects_dir" ]; then
        local -a projects
        projects=($projects_dir/*(/:t))
        _describe 'projects' projects
    fi
}

_numchuck "$@"
