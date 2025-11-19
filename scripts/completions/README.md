# Shell Completion for pychuck

This directory contains shell completion scripts for the `pychuck` CLI.

## Features

- Complete subcommands: `edit`, `repl`, `run`, `version`, `info`
- Complete command-line options for each subcommand
- Complete `.ck` file paths
- Complete project names from `~/.pychuck/projects/`
- Suggest common sample rates and channel counts

## Installation

### Bash

**Option 1: Per-user installation**

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
source /path/to/pychuck/completions/pychuck-completion.bash
```

**Option 2: System-wide installation**

```bash
sudo cp completions/pychuck-completion.bash /etc/bash_completion.d/pychuck
```

Then restart your shell or run:

```bash
source ~/.bashrc
```

### Zsh

**Option 1: Using fpath**

1. Copy the completion file to a directory in your `$fpath`:

```bash
# Find your fpath directories
echo $fpath

# Copy to one of them (example)
sudo cp completions/pychuck-completion.zsh /usr/local/share/zsh/site-functions/_pychuck
```

2. Reload completions:

```bash
compinit
```

**Option 2: Manual sourcing**

Add to your `~/.zshrc`:

```zsh
fpath=(/path/to/pychuck/completions $fpath)
autoload -Uz compinit && compinit
```

Then restart your shell or run:

```bash
source ~/.zshrc
```

## Usage Examples

After installation, you can use tab completion:

```bash
# Complete subcommands
pychuck <TAB>
# Shows: edit repl run version info

# Complete options for edit
pychuck edit --<TAB>
# Shows: --project --start-audio

# Complete .ck files
pychuck run <TAB>
# Shows .ck files in current directory

# Complete sample rates
pychuck run file.ck --srate <TAB>
# Shows: 22050 44100 48000 96000

# Complete project names
pychuck edit --project <TAB>
# Shows projects from ~/.pychuck/projects/
```

## Supported Completions

### Subcommands

- `edit` - Multi-tab editor
- `repl` - Interactive REPL
- `tui` - Alias for repl
- `run` - Execute files
- `version` - Show version
- `info` - Show system info

### Options by Subcommand

**edit**:
- `--project` - Completes with existing project names
- `--start-audio` - Flag (no completion)
- Files: Completes `.ck` files

**repl / tui**:
- `--start-audio` - Flag
- `--no-smart-enter` - Flag
- `--no-sidebar` - Flag
- `--project` - Completes with existing project names
- Files: Completes `.ck` files

**run**:
- `--srate` - Suggests: 22050, 44100, 48000, 96000
- `--channels` - Suggests: 1, 2
- `--silent` - Flag
- `--duration` - Numeric (no completion)
- Files: Completes `.ck` files

**version / info**:
- No options

## Testing

Test completion without installing:

```bash
# Bash
source completions/pychuck-completion.bash
pychuck <TAB>

# Zsh
fpath=(completions $fpath)
autoload -Uz compinit && compinit
pychuck <TAB>
```

## Troubleshooting

**Bash: Completion not working**

1. Check if bash-completion is installed:
   ```bash
   # macOS
   brew install bash-completion

   # Ubuntu/Debian
   sudo apt-get install bash-completion
   ```

2. Ensure it's enabled in your shell config

**Zsh: Completion not working**

1. Check your fpath:
   ```bash
   echo $fpath
   ```

2. Rebuild completion cache:
   ```bash
   rm ~/.zcompdump*
   compinit
   ```

3. Check permissions:
   ```bash
   # Completion files should be readable
   chmod 644 /path/to/_pychuck
   ```

## Development

To modify completions:

1. Edit the appropriate completion file
2. Test by sourcing the file
3. Verify all subcommands and options are covered
4. Test edge cases (files with spaces, special characters)

### Adding New Subcommands

When adding a new subcommand to `pychuck`:

1. Add to `commands` list in bash completion
2. Add to `commands` array in zsh completion
3. Add case handler with appropriate options
4. Test completion behavior
