"""An exception raised in a Python callback must not unwind through the VM.

It goes to sys.unraisablehook, and the VM keeps running.
"""

import subprocess
import sys
import textwrap

import pytest

from numchuck import Chuck, _numchuck


class Boom(Exception):
    pass


def boom(*args):
    raise Boom("boom")


@pytest.fixture
def chuck():
    c = Chuck()
    yield c
    c.close()


def assert_reported(unraisable, count=1):
    assert len(unraisable) == count
    assert all(isinstance(u.exc_value, Boom) for u in unraisable)


GLOBALS = """
    global int i; global float f; global string s;
    global int ia[2]; global float fa[2];
    1 => i; 1.5 => f; "x" => s;
    1::day => now;
"""


@pytest.mark.parametrize(
    "getter",
    ["get_global_int", "get_global_float", "get_global_string",
     "get_global_int_array", "get_global_float_array"],
)
def test_getter(chuck, unraisable, getter):
    name = {"get_global_int": "i", "get_global_float": "f",
            "get_global_string": "s", "get_global_int_array": "ia",
            "get_global_float_array": "fa"}[getter]
    chuck.compile(GLOBALS)
    chuck.run(1)
    getattr(chuck.raw, getter)(name, boom)
    chuck.run(1)
    assert_reported(unraisable)
    # the VM still answers
    assert chuck.get_float("f") == 1.5


def test_event_listener_keeps_firing(chuck, unraisable):
    chuck.compile("global Event e; while (true) { e.broadcast(); 1::samp => now; }")
    chuck.on_event("e", boom)
    chuck.run(3)
    assert_reported(unraisable, 3)


def test_shred_watcher(chuck, unraisable):
    chuck.on_shred(boom, _numchuck.SHRED_WATCH_SPORK)
    chuck.compile("1::samp => now;")
    chuck.compile("1::samp => now;")
    chuck.run(1)
    assert_reported(unraisable, 2)


def test_chout_and_cherr(chuck, unraisable):
    chuck.set_stdout_callback(boom)
    chuck.set_stderr_callback(boom)
    chuck.compile('chout <= "a" <= IO.nl(); cherr <= "b" <= IO.nl(); 1::samp => now;')
    chuck.run(2)
    assert len(unraisable) >= 2
    assert all(isinstance(u.exc_value, Boom) for u in unraisable)
    assert chuck.shreds == []


def test_global_stderr_callback(chuck, unraisable):
    _numchuck.ChucK.set_stderr_callback(boom)
    try:
        chuck.compile('<<< "a" >>>; 1::samp => now;')
        chuck.run(2)
    finally:
        _numchuck.ChucK.set_stderr_callback(None)
    assert len(unraisable) >= 1
    assert all(isinstance(u.exc_value, Boom) for u in unraisable)


@pytest.mark.realtime
def test_realtime_event_listener_raises_on_audio_thread():
    code = """
        import sys, time
        from numchuck import Chuck, _numchuck
        seen = []
        sys.unraisablehook = seen.append
        c = Chuck(sample_rate=44100, input_channels=0, output_channels=2)
        c.compile("global Event e; while (true) { e.broadcast(); 10::ms => now; }")
        def boom():
            raise ValueError("boom")
        c.on_event("e", boom)
        assert _numchuck.start_audio(c.raw, sample_rate=44100, num_dac_channels=2)
        try:
            time.sleep(0.3)
        finally:
            _numchuck.stop_audio()
            _numchuck.shutdown_audio()
        assert len(seen) > 5, len(seen)
        c.close()
        print("ok")
    """
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
