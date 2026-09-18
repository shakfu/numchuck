# TODO

## Critical

## High

### Known Crashes

- [ ] **Stack over-read in the GVerb chugin** (`thirdparty/chugins/GVerb/gverbdefs.h:114`)
  - AddressSanitizer reports `stack-buffer-overflow`, an 8-byte READ of the 4-byte
    stack float `x` in `gverb_do()` (inlined into `GVerb::tick`), ten occurrences per
    run of the suite
  - Real undefined behaviour, but a read of adjacent stack within the same frame, so
    it is not a plausible cause of a segfault and was left alone rather than guessed at
  - Fixing it needs a `scripts/patches/chugins/` patch, as GVerb is vendored upstream

### Memory Leaks

- [ ] **Chugin objects are never destroyed when a VM is shut down with live shreds**
  (`thirdparty/chuck/core/chuck_vm.cpp`, `Chuck_VM::shutdown()` / `removeAll()`)
  - A chugin's `CK_DLL_DTOR` runs when its shred *ends on its own* while the VM is
    running, but not when the shred is still alive at teardown. `remove_all_shreds()`
    followed by `shutdown()` never invokes it, so the C++ object the chugin's ctor
    allocated is leaked along with everything it owns
  - Measured with an instrumented ConvRev (an `fprintf` in `convrev_ctor`,
    `convrev_dtor` and `~ConvRev`), creating and tearing down VMs in a loop:

    | teardown path | `convrev_dtor` | RSS per VM |
    | --- | --- | --- |
    | shred ends naturally | fires | ~4.2 MB |
    | shred live at shutdown | never fires | ~23.6 MB |

    so ~19 MB per VM is the un-destroyed ConvRev -- mostly its 5513 FFT partition
    segments. The ~4.2 MB that remains when the dtor *does* run is a separate
    residual leak, not yet chased
  - General to every chugin, not specific to ConvRev; ConvRev is only where it was
    also a crash, because it is the sole bundled chugin that owns a thread, and the
    abandoned object means its `~ConvRev()` join never happens. That crash is fixed
    separately by `scripts/patches/0004-chugin-rtld-nodelete.patch`, which makes the
    orphaned thread survivable -- it does not address this leak
  - Not a use-after-free: because nothing is ever freed, the orphaned worker only
    ever writes to memory that stays allocated. This is why patching ConvRev's
    threading was considered and rejected
  - Ruled out as a workaround: calling `run()` again after `remove_all_shreds()` so
    the VM can process the removal message. The dtor still never fires and the leak
    is unchanged, so removal is not merely deferred
  - Matters for a long-lived host that creates and destroys VMs; harmless for the
    test suite, which exits. `tests/test_examples.py::test_chugin_convrev_example`
    hits it because `examples/convrev/ConvRev.ck` ends in `while(true)`, so its
    shred is always live at teardown

### Real-time Audio: Global UGen Taps

- [ ] **Remove the audio-thread allocation in tap capture** (`src/_numchuck.cpp`, `capture_taps`)
  - ChucK keeps `m_global_ugens` private (`chuck_globals.h:356`) and exposes only
    `getGlobalUGenSamples(const char *, ...)`, so every capture builds a `std::string`
    temporary for the map lookup -- heap-free only when the small-string optimization
    covers the name
  - Bounded in count (one lookup per active tap per block, taps capped at 8) and
    chuck-max's perform routine does the same, but it is still a potentially
    unbounded-latency call on the audio thread
  - Fix: vendored patch under `scripts/patches/` exposing a UGen accessor, resolve the
    `Chuck_UGen *` once in `add_tap()`, then read the buffer directly per block.
    `apply_patches()` in `scripts/update.sh` re-applies it after a chuck update

## Medium

- [ ] enable advanced chugins {faust, warpbuf, fluidsynth}

### REPL Issues

- [ ] **Fix multiline detection for string literals/comments** (`repl.py:387-437`)
  - Substring checks (`"=>" in text`) false-trigger on string literals and comments
  - Use a ChucK-aware lexer pass or at minimum skip strings/comments

- [ ] **Fix completer `start_position` for `?`/`::` suffixes** (`completer.py:203-215`)
  - `start_position=-len(text)` should be `-len(prefix)`, causing incorrect replacement

- [ ] **Fix history file setup order** (`repl.py:377, 440`)
  - `FileHistory(get_history_file())` called before `ensure_numchuck_directories()`
  - Parent directory may not exist yet

- [ ] **Validate `EDITOR` env var in `edit_shred`** (`commands.py:351-389`)
  - Editor binary used directly with no validation or error handling
  - Temp file cleanup is best-effort

- [ ] **Deduplicate window visibility state** (`repl.py:217-225`, `common.py:292-295`)
  - Two independent sets of flags (`show_help_window` vs `show_help`) not synchronized
  - Risks UI state desync

- [ ] **Cap autocomplete results** (`completer.py:165-259`)
  - No result limit; single-character prefix yields all matching ChucK identifiers
  - Cap at ~50 results

## Low

### REPL Issues

- [ ] **Use `deque` for log trimming** (`repl.py:545-561`, `common.py:534-537`)
  - `list.pop(0)` is O(n) per message; `collections.deque(maxlen=N)` is O(1)

- [ ] **Allow error bar to wrap or grow** (`repl.py:486-493`)
  - `height=D.exact(1)` truncates long compilation errors

- [ ] **Update session source after `edit_shred`** (`session.py:48-85`, `commands.py:351-389`)
  - Replaced shred code not reflected in `session.shreds[id]["source"]`

- [ ] **Document smart enter rules** (`repl.py:383-437`)
  - Multiline logic undocumented; help text and `--no-smart-enter` don't explain actual behavior

- [ ] **Add `--strict` mode for stdin REPL** (`repl.py:84-133`)
  - Currently fail-soft: errors set exit code but processing continues

- [ ] **Break reference cycle in log callbacks** (`common.py:401-413`)
  - `log_callback` closure captures `self`, ChucK holds reference back; use `weakref`

### Future Enhancements: Tooling

- [ ] **LSP server for IDE integration**
  - Language Server Protocol implementation for ChucK
  - Would enable VS Code, Neovim, etc. integration
  - Features: syntax errors, completions, hover docs

### Future Enhancements: Documentation

- [ ] **Interactive tutorial**
  - Step-by-step livecoding introduction
  - Could be a guided REPL mode or web-based

- [ ] **Cookbook**
  - Common patterns and recipes
  - Examples: FM synthesis, drum machines, effects chains

- [ ] **Video documentation**
  - Screen recordings of livecoding sessions
  - Tutorial videos showing REPL/editor workflows
