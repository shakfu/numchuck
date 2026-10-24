"""Python callbacks stored by the binding are only touched with the GIL held.

Each case runs in a subprocess: the failure modes are a crash or a hang.
"""

import subprocess
import sys
import textwrap

import pytest


def run_python(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_listener_released_by_removal_may_register_another():
    # The registry holds the only reference, so removal frees the listener,
    # and its __del__ registers another callback. Freeing it inside the
    # registry lock deadlocked.
    result = run_python("""
        from numchuck import Chuck
        c = Chuck()
        c.compile("global Event e; 1::day => now;")
        c.run(1)
        freed = []

        class Listener:
            def __call__(self):
                pass

            def __del__(self):
                freed.append(c.on_event("e", lambda: None))

        for _ in range(50):
            c.stop_listening_for_event("e", c.on_event("e", Listener()))
        assert len(freed) == 50, freed
        c.close()
        print("ok")
    """)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


@pytest.mark.realtime
def test_realtime_one_shot_callback_released_on_audio_thread():
    # The audio thread runs the callback and drops the registry's reference,
    # the only one, so __del__ runs there too. Without the GIL that crashed.
    result = run_python("""
        import time
        from numchuck import Chuck, _numchuck
        c = Chuck(sample_rate=44100, input_channels=0, output_channels=2)
        c.compile("global float x; 1.5 => x; while (true) 1::ms => now;")
        c.run(1)  # set x before the first request
        got, freed = [], []

        class Once:
            def __call__(self, value):
                got.append(value)

            def __del__(self):
                freed.append(1)

        assert _numchuck.start_audio(c.raw, sample_rate=44100, num_dac_channels=2)
        try:
            for _ in range(100):
                c.get_float_async("x", Once())
                time.sleep(0.002)
            deadline = time.monotonic() + 2
            while len(freed) < 100 and time.monotonic() < deadline:
                time.sleep(0.01)
        finally:
            _numchuck.stop_audio()
            _numchuck.shutdown_audio()
        assert got == [1.5] * 100, len(got)
        assert len(freed) == 100, len(freed)
        c.close()
        print("ok")
    """)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_exit_with_callbacks_still_registered():
    result = run_python("""
        from numchuck import Chuck, _numchuck
        _numchuck.ChucK.set_stdout_callback(lambda msg: None)
        _numchuck.ChucK.set_stderr_callback(lambda msg: None)
        c = Chuck()
        c.compile("global Event e; 1::day => now;")
        c.on_event("e", lambda: None)
        c.on_shred(lambda code, sid, name: None)
        c.set_stdout_callback(lambda msg: None)
        print("ok")
    """)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
