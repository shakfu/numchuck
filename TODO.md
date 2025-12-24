# TODO

- [ ] enable advanced chugins {faust, warpbug, fluidsynth}

- [x] complete api wrapping, missing a bunch of params, methods, and callbacks

---

## From Code Review

Remaining tasks from recent code review.

### C++ Binding Layer

- [x] **Memory leak potential in `replace_shred`** (`src/_numchuck.cpp`)
  - Fixed: Now uses `std::unique_ptr` for exception safety during message construction

### Python API

- [x] **Improve error propagation for sync getters** (`src/numchuck/api.py`)
  - Fixed: Error messages now explain that callback wasn't invoked and suggest increasing `run_frames`

### TUI Components

- [x] **Inconsistent error handling in cleanup** (`src/numchuck/tui/repl.py`)
  - Fixed: Now catches `RuntimeError` for ChucK ops, `(RuntimeError, OSError)` for audio ops

- [x] **Potential race condition in editor tab switching** (`src/numchuck/tui/editor.py`)
  - Resolved: Added documentation explaining prompt_toolkit is single-threaded (no actual race)

### Test Suite

- [x] **Expand test_api.py coverage**
  - Added 11 new tests: event callbacks (5), advance method (2), buffer reuse modes (4)
  - Total test count: 213 (up from 202)

- [x] **Fix flaky test pattern**
  - Fixed `try/except pass` patterns in test_global_events.py, test_realtime_audio.py, test_error_handling.py
  - Tests now have explicit assertions documenting expected behavior

### Build / CI

- [x] **Investigate skipped platform tests** (`wheels.yml`)
  - Restored testing on macosx_arm64
  - Windows skipped due to access violation in ChucK VM cleanup
  - manylinux_aarch64 skipped (cross-compiled, no native runner)
  - wavfile tests skipped in CI (WvOut timing issues)

- [x] **Fix Windows access violation** (implemented, needs testing)
  - Crash occurs during ChucK VM destruction/cleanup
  - Affects all Python versions on Windows
  - Fixes implemented based on chuck-max comparison:
    1. Added explicit `shutdown()` method with `vm->shutdown()` call
    2. Added `Chuck_VM_Object::unlock_all()/lock_all()` around callback cleanup
    3. Added post-stop delay for Windows audio threads (100ms default)
    4. Added `cleanup_instance_callbacks()` for proper per-instance cleanup
  - Python API: `Chuck.close()` method for explicit shutdown
