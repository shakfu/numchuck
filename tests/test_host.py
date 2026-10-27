"""Tests for the host classes bound into every VM: Host, HostBuffer, HostBufPlay."""

import subprocess
import sys

import numpy as np
import pytest

from numchuck import Chuck

SR = 48000


@pytest.fixture
def chuck():
    c = Chuck(sample_rate=SR, output_channels=1)
    yield c
    c.close()


def sends(chuck):
    """Record (name, value, now) for each Host.msg."""
    got = []
    raw = chuck.raw
    chuck.on_msg(lambda name, value: got.append((name, value, raw.now())))
    return got


def results(got):
    return {name: value for name, value, _ in got}


# -----------------------------------------------------------------------------
# Host.msg


class TestHostMsg:
    def test_reaches_callback_at_logical_time(self, chuck):
        got = sends(chuck)
        chuck.compile('Host.msg("a", 1.5); 100::samp => now; Host.msg("b", 2);')
        chuck.run(200)
        assert got == [("a", 1.5, 0.0), ("b", 2.0, 100.0)]

    def test_no_callback_is_a_no_op(self, chuck):
        chuck.compile('Host.msg("a", 1);')
        chuck.run(10)

    def test_none_clears(self, chuck):
        got = sends(chuck)
        chuck.on_msg(None)
        chuck.compile('Host.msg("a", 1);')
        chuck.run(10)
        assert got == []

    def test_replacing_callback(self, chuck):
        first = sends(chuck)
        second = sends(chuck)
        chuck.compile('Host.msg("a", 1);')
        chuck.run(10)
        assert first == []
        assert [g[:2] for g in second] == [("a", 1.0)]

    def test_rejects_non_callable(self, chuck):
        with pytest.raises(TypeError):
            chuck.on_msg(42)

    def test_exception_does_not_stop_the_vm(self, chuck, monkeypatch):
        unraisable = []
        monkeypatch.setattr(sys, "unraisablehook", unraisable.append)
        seen = []

        def callback(name, value):
            seen.append(name)
            if name == "boom":
                raise ValueError("boom")

        chuck.on_msg(callback)
        chuck.compile('Host.msg("boom", 0); 1::samp => now; Host.msg("after", 0);')
        chuck.run(10)
        assert seen == ["boom", "after"]
        assert len(unraisable) == 1
        assert isinstance(unraisable[0].exc_value, ValueError)

    def test_instances_are_separate(self):
        a, b = Chuck(), Chuck()
        try:
            got_a, got_b = sends(a), sends(b)
            a.compile('Host.msg("from_a", 1);')
            b.compile('Host.msg("from_b", 2);')
            a.run(10)
            b.run(10)
            assert [g[0] for g in got_a] == ["from_a"]
            assert [g[0] for g in got_b] == ["from_b"]
        finally:
            a.close()
            b.close()

    def test_survives_clear(self, chuck):
        got = sends(chuck)
        chuck.clear()
        chuck.compile('Host.msg("a", 1);')
        chuck.run(10)
        assert [g[0] for g in got] == ["a"]

    def test_close_releases_callback(self):
        c = Chuck()
        callback = lambda name, value: None  # noqa: E731
        before = sys.getrefcount(callback)
        c.on_msg(callback)
        assert sys.getrefcount(callback) > before
        c.close()
        assert sys.getrefcount(callback) == before

    def test_overloads(self, chuck):
        got = sends(chuck)
        chuck.compile("""
            Host.msg("b"); Host.msg("f", 2.5); Host.msg("s", "kick.wav");
            Host.msg("l", [1.0, -2.0, 3.5]);
        """)
        chuck.run(1)
        assert [g[:2] for g in got] == [
            ("b", None), ("f", 2.5), ("s", "kick.wav"), ("l", [1.0, -2.0, 3.5]),
        ]
        assert type(got[1][1]) is float
        assert type(got[2][1]) is str
        assert type(got[3][1]) is list

    def test_int_literal_resolves_to_float(self, chuck):
        got = sends(chuck)
        chuck.compile('Host.msg("i", 1);')
        chuck.run(1)
        assert got[0][:2] == ("i", 1.0)
        assert type(got[0][1]) is float

    def test_list_whole_and_empty(self, chuck):
        got = sends(chuck)
        chuck.compile("""
            float big[100]; for (0 => int i; i < 100; i++) i => big[i];
            Host.msg("big", big);
            float empty[0]; Host.msg("empty", empty);
        """)
        chuck.run(1)
        assert got[0][1] == [float(i) for i in range(100)]
        assert got[1][1] == []


# -----------------------------------------------------------------------------
# Host.sendBang / sendFloat / sendSymbol / sendList -> on_receive


class TestHostReceive:
    def receive(self, chuck, name):
        """Record (value, now) for each Host.send* to name."""
        got = []
        raw = chuck.raw
        chuck.on_receive(name, lambda value: got.append((value, raw.now())))
        return got

    def test_each_type(self, chuck):
        b, f, s, lst = (self.receive(chuck, n) for n in ("b", "f", "s", "l"))
        chuck.compile("""
            Host.sendBang("b"); Host.sendFloat("f", 2.5);
            Host.sendSymbol("s", "kick.wav"); Host.sendList("l", [1.0, -2.0, 3.5]);
        """)
        chuck.run(10)
        assert b == [(None, 0.0)]
        assert f == [(2.5, 0.0)]
        assert s == [("kick.wav", 0.0)]
        assert lst == [([1.0, -2.0, 3.5], 0.0)]

    def test_one_callback_takes_every_type(self, chuck, unraisable):
        # a [receive] accepts any message, so one callback must too
        got = self.receive(chuck, "x")
        chuck.compile("""
            Host.sendBang("x"); Host.sendFloat("x", 1);
            Host.sendSymbol("x", "s"); Host.sendList("x", [2.0]);
        """)
        chuck.run(10)
        assert [value for value, _ in got] == [None, 1.0, "s", [2.0]]
        assert unraisable == []

    def test_at_logical_time(self, chuck):
        got = self.receive(chuck, "t")
        chuck.compile('Host.sendBang("t"); 100::samp => now; Host.sendBang("t");')
        chuck.run(200)
        assert [now for _, now in got] == [0.0, 100.0]

    def test_whole_and_empty_lists(self, chuck):
        got = self.receive(chuck, "l")
        chuck.compile("""
            float big[1000]; for (0 => int i; i < 1000; i++) i => big[i];
            Host.sendList("l", big);
            float empty[0]; Host.sendList("l", empty);
        """)
        chuck.run(10)
        assert got[0][0] == [float(i) for i in range(1000)]
        # distinct from a bang, which is None
        assert got[1][0] == []

    def test_several_callbacks_in_order(self, chuck):
        order = []
        chuck.on_receive("x", lambda v: order.append(("first", v)))
        chuck.on_receive("x", lambda v: order.append(("second", v)))
        chuck.compile('Host.sendFloat("x", 1);')
        chuck.run(10)
        assert order == [("first", 1.0), ("second", 1.0)]

    def test_unknown_name_is_skipped(self, chuck):
        got = self.receive(chuck, "x")
        chuck.compile('Host.sendFloat("nobody", 1); Host.sendFloat("x", 2);')
        chuck.run(10)
        assert [value for value, _ in got] == [2.0]

    def test_remove(self, chuck):
        got = []
        cid = chuck.on_receive("x", got.append)
        assert chuck.remove_receiver("x", cid) is True
        assert chuck.remove_receiver("x", cid) is False
        assert chuck.remove_receiver("never", cid) is False
        chuck.compile('Host.sendFloat("x", 1);')
        chuck.run(10)
        assert got == []

    def test_callback_removes_itself(self, chuck):
        got = []
        ids = {}

        def once(value):
            got.append(value)
            chuck.remove_receiver("x", ids["once"])

        ids["once"] = chuck.on_receive("x", once)
        chuck.on_receive("x", lambda v: got.append(-v))
        chuck.compile('Host.sendFloat("x", 1); Host.sendFloat("x", 2);')
        chuck.run(10)
        assert got == [1.0, -1.0, -2.0]

    def test_exception_is_reported(self, chuck, monkeypatch):
        unraisable = []
        monkeypatch.setattr(sys, "unraisablehook", unraisable.append)
        got = []

        def boom(value):
            raise ValueError("boom")

        chuck.on_receive("x", boom)
        chuck.on_receive("x", lambda value: got.append(1))
        chuck.compile('Host.sendBang("x");')
        chuck.run(10)
        assert got == [1]
        assert len(unraisable) == 1 and isinstance(unraisable[0].exc_value, ValueError)

    def test_instances_are_separate(self):
        a, b = Chuck(), Chuck()
        try:
            got_a = self.receive(a, "x")
            got_b = self.receive(b, "x")
            a.compile('Host.sendFloat("x", 1);')
            b.compile('Host.sendFloat("x", 2);')
            a.run(10)
            b.run(10)
            assert [value for value, _ in got_a] == [1.0]
            assert [value for value, _ in got_b] == [2.0]
        finally:
            a.close()
            b.close()

    def test_close_releases_callbacks(self):
        c = Chuck()
        callback = lambda value: None  # noqa: E731
        before = sys.getrefcount(callback)
        c.on_receive("x", callback)
        c.on_receive("y", callback)
        assert sys.getrefcount(callback) == before + 2
        c.close()
        assert sys.getrefcount(callback) == before

    def test_remove_releases_callback(self, chuck):
        callback = lambda value: None  # noqa: E731
        before = sys.getrefcount(callback)
        cid = chuck.on_receive("x", callback)
        chuck.remove_receiver("x", cid)
        assert sys.getrefcount(callback) == before

    def test_sibling_host_examples_compile(self, chuck):
        # the Host.send* calls chuck-max and pd-chuck ship examples for
        ok, _ = chuck.compile("""
            Host.sendBang("tick"); Host.sendFloat("freq", 1);
            Host.sendSymbol("range", "low"); Host.sendList("pair", [1.0, 0.2]);
        """)
        assert ok


# -----------------------------------------------------------------------------
# HostBuffer


class TestHostBuffer:
    def query(self, chuck, body):
        got = sends(chuck)
        chuck.compile('HostBuffer b; b.name("buf") => string n;\n' + body)
        chuck.run(10)
        return results(got)

    def test_not_ready_without_array(self, chuck):
        r = self.query(chuck, """
            Host.msg("ready", b.ready()); Host.msg("frames", b.frames());
            Host.msg("peek", b.peek(0)); b.poke(0, 1.0);
        """)
        assert r == {"ready": 0, "frames": 0, "peek": 0}

    def test_shape_and_rate(self, chuck):
        chuck.set_buffer("buf", np.zeros((5, 3), dtype=np.float32), sample_rate=22050)
        r = self.query(chuck, """
            Host.msg("ready", b.ready()); Host.msg("frames", b.frames());
            Host.msg("chans", b.channels()); Host.msg("sr", b.sampleRate());
        """)
        assert r == {"ready": 1, "frames": 5, "chans": 3, "sr": 22050}

    def test_1d_is_one_channel_at_vm_rate(self, chuck):
        chuck.set_buffer("buf", np.zeros(4, dtype=np.float32))
        r = self.query(chuck, 'Host.msg("chans", b.channels()); Host.msg("sr", b.sampleRate());')
        assert r == {"chans": 1, "sr": SR}

    def test_peek_and_poke_in_place(self, chuck):
        buf = np.arange(8, dtype=np.float32).reshape(4, 2)
        chuck.set_buffer("buf", buf)
        r = self.query(chuck, """
            Host.msg("p0", b.peek(1)); Host.msg("p21", b.peek(2, 1));
            b.poke(3, -1.0); b.poke(0, 1, -2.0);
        """)
        assert r == {"p0": 2, "p21": 5}
        assert buf.tolist() == [[0, -2], [2, 3], [4, 5], [-1, 7]]

    def test_python_writes_are_visible(self, chuck):
        buf = np.zeros(2, dtype=np.float32)
        chuck.set_buffer("buf", buf)
        buf[1] = 0.25
        assert self.query(chuck, 'Host.msg("p", b.peek(1));') == {"p": 0.25}

    def test_out_of_range(self, chuck):
        buf = np.arange(4, dtype=np.float32).reshape(2, 2)
        chuck.set_buffer("buf", buf)
        r = self.query(chuck, """
            Host.msg("f", b.peek(2)); Host.msg("neg", b.peek(-1));
            Host.msg("c", b.peek(0, 2));
            b.poke(2, 9.0); b.poke(-1, 9.0); b.poke(0, 2, 9.0); b.poke(0, -1, 9.0);
        """)
        assert r == {"f": 0, "neg": 0, "c": 0}
        assert buf.tolist() == [[0, 1], [2, 3]]

    def test_remove(self, chuck):
        chuck.set_buffer("buf", np.ones(2, dtype=np.float32))
        assert chuck.remove_buffer("buf") is True
        assert chuck.remove_buffer("buf") is False
        assert chuck.remove_buffer("never") is False
        assert self.query(chuck, 'Host.msg("ready", b.ready());') == {"ready": 0}

    def test_replace(self, chuck):
        chuck.set_buffer("buf", np.ones(2, dtype=np.float32))
        chuck.set_buffer("buf", np.full(3, 7, dtype=np.float32))
        r = self.query(chuck, 'Host.msg("n", b.frames()); Host.msg("p", b.peek(2));')
        assert r == {"n": 3, "p": 7}

    def test_registered_after_name(self, chuck):
        got = sends(chuck)
        chuck.compile("""
            HostBuffer b; b.name("late");
            Host.msg("before", b.ready());
            10::samp => now;
            Host.msg("after", b.peek(0));
        """)
        chuck.run(5)
        chuck.set_buffer("late", np.full(1, 3, dtype=np.float32))
        chuck.run(10)
        assert results(got) == {"before": 0, "after": 3}

    def test_name_round_trip(self, chuck):
        got = sends(chuck)
        chuck.compile("""
            HostBuffer b;
            if (b.name() == "") Host.msg("empty", 1);
            if (b.name("x") == "x" && b.name() == "x") Host.msg("set", 1);
        """)
        chuck.run(10)
        assert results(got) == {"empty": 1, "set": 1}

    def test_slots_persist_across_clear(self, chuck):
        chuck.set_buffer("buf", np.full(1, 4, dtype=np.float32))
        chuck.clear()
        assert self.query(chuck, 'Host.msg("p", b.peek(0));') == {"p": 4}

    def test_slot_limit(self, chuck):
        for i in range(64):
            chuck.set_buffer(f"b{i}", np.zeros(1, dtype=np.float32))
        chuck.set_buffer("b0", np.zeros(1, dtype=np.float32))  # reuse by name
        with pytest.raises(RuntimeError, match="64"):
            chuck.set_buffer("one_more", np.zeros(1, dtype=np.float32))
        got = sends(chuck)
        chuck.compile('HostBuffer b; if (b.name("other") == "") Host.msg("refused", 1);')
        chuck.run(10)
        assert results(got) == {"refused": 1}

    def test_instances_are_separate(self):
        a, b = Chuck(), Chuck()
        try:
            a.set_buffer("buf", np.full(1, 1, dtype=np.float32))
            got = sends(b)
            b.compile('HostBuffer x; x.name("buf"); Host.msg("ready", x.ready());')
            b.run(10)
            assert results(got) == {"ready": 0}
        finally:
            a.close()
            b.close()

    @pytest.mark.parametrize(
        "array, error",
        [
            (np.zeros(4, dtype=np.float64), TypeError),
            (np.zeros((4, 2), dtype=np.float32)[:, 0], TypeError),
            (np.zeros((2, 2, 2), dtype=np.float32), ValueError),
            (np.zeros(0, dtype=np.float32), ValueError),
            ([0.0, 1.0], TypeError),
        ],
        ids=["float64", "strided", "3d", "empty", "list"],
    )
    def test_rejects(self, chuck, array, error):
        with pytest.raises(error):
            chuck.set_buffer("buf", array)

    def test_rejects_read_only(self, chuck):
        array = np.zeros(4, dtype=np.float32)
        array.flags.writeable = False
        with pytest.raises(TypeError):
            chuck.set_buffer("buf", array)

    def test_close_releases_arrays(self):
        c = Chuck()
        array = np.zeros(4, dtype=np.float32)
        before = sys.getrefcount(array)
        c.set_buffer("buf", array)
        assert sys.getrefcount(array) > before
        c.close()
        assert sys.getrefcount(array) == before

    def test_remove_releases_array(self, chuck):
        array = np.zeros(4, dtype=np.float32)
        before = sys.getrefcount(array)
        chuck.set_buffer("buf", array)
        chuck.remove_buffer("buf")
        assert sys.getrefcount(array) == before

    def test_garbage_collected_instances(self):
        # a dropped, unclosed instance keeps its arrays until its address is
        # reused; churning instances must neither crash nor cross over
        for i in range(20):
            c = Chuck()
            c.set_buffer("buf", np.full(1, i, dtype=np.float32))
            got = sends(c)
            c.compile('HostBuffer b; b.name("buf"); Host.msg("p", b.peek(0));')
            c.run(10)
            assert results(got) == {"p": i}
            del c

    def test_exit_with_registered_array(self):
        code = (
            "import numpy as np\n"
            "from numchuck import Chuck\n"
            "c = Chuck()\n"
            "c.set_buffer('b', np.zeros(4, dtype=np.float32))\n"
            "c.on_msg(lambda n, v: None)\n"
        )
        result = subprocess.run([sys.executable, "-c", code], timeout=60)
        assert result.returncode == 0


# -----------------------------------------------------------------------------
# HostBufPlay


def play(chuck, setup, frames):
    chuck.compile("HostBufPlay p => dac;\n" + setup + "\n1::day => now;")
    return chuck.run(frames).tolist()


class TestHostBufPlay:
    @pytest.fixture
    def ramp(self, chuck):
        chuck.set_buffer("ramp", np.array([0, 1, 2, 3], dtype=np.float32))

    def test_one_shot(self, chuck, ramp):
        assert play(chuck, 'p.name("ramp");', 6) == [0, 1, 2, 3, 0, 0]

    def test_loop(self, chuck, ramp):
        assert play(chuck, 'p.name("ramp"); 1 => p.loop;', 6) == [0, 1, 2, 3, 0, 1]

    def test_half_rate_interpolated(self, chuck, ramp):
        out = play(chuck, 'p.name("ramp"); 0.5 => p.rate;', 9)
        assert out == [0, 0.5, 1, 1.5, 2, 2.5, 3, 3, 0]

    def test_half_rate_uninterpolated(self, chuck, ramp):
        out = play(chuck, 'p.name("ramp"); 0.5 => p.rate; 0 => p.interp;', 5)
        assert out == [0, 0, 1, 1, 2]

    def test_interpolation_wraps_at_loop_point(self, chuck, ramp):
        out = play(chuck, 'p.name("ramp"); 0.5 => p.rate; 1 => p.loop; 3 => p.pos;', 3)
        assert out == [3, 1.5, 0]

    def test_backward(self, chuck, ramp):
        out = play(chuck, 'p.name("ramp"); -1 => p.rate; 3 => p.pos;', 6)
        assert out == [3, 2, 1, 0, 0, 0]

    def test_channel(self, chuck):
        chuck.set_buffer("st", np.array([[1, 10], [2, 20]], dtype=np.float32))
        assert play(chuck, 'p.name("st"); 1 => p.channel;', 3) == [10, 20, 0]

    def test_bad_channel_is_silent(self, chuck):
        chuck.set_buffer("st", np.ones((2, 2), dtype=np.float32))
        assert play(chuck, 'p.name("st"); 2 => p.channel;', 2) == [0, 0]

    def test_buffer_rate(self, chuck):
        chuck.set_buffer("ramp", np.array([0, 1, 2, 3], dtype=np.float32), sample_rate=SR / 2)
        assert play(chuck, 'p.name("ramp");', 4) == [0, 0.5, 1, 1.5]

    def test_missing_then_registered(self, chuck):
        assert play(chuck, 'p.name("later");', 2) == [0, 0]
        chuck.set_buffer("later", np.array([5, 6], dtype=np.float32))
        assert chuck.run(3).tolist() == [5, 6, 0]

    def test_removed_mid_play_holds_position(self, chuck):
        buf = np.array([0, 1, 2, 3], dtype=np.float32)
        chuck.set_buffer("ramp", buf)
        assert play(chuck, 'p.name("ramp");', 2) == [0, 1]
        chuck.remove_buffer("ramp")
        assert chuck.run(2).tolist() == [0, 0]
        chuck.set_buffer("ramp", buf)
        assert chuck.run(2).tolist() == [2, 3]

    def test_name_restarts(self, chuck, ramp):
        chuck.compile("""
            global HostBufPlay p => dac; p.name("ramp");
            2::samp => now; p.name("ramp"); 1::day => now;
        """)
        assert chuck.run(4).tolist() == [0, 1, 0, 1]

    def test_shares_slots_with_hostbuffer(self, chuck, ramp):
        got = sends(chuck)
        out = play(chuck, """
            p.name("ramp");
            HostBuffer b; b.name("ramp"); b.poke(1, 9.0);
            Host.msg("frames", p.frames()); Host.msg("ready", p.ready());
        """, 2)
        assert out == [0, 9]
        assert results(got) == {"frames": 4, "ready": 1}


# -----------------------------------------------------------------------------
# real-time audio


@pytest.mark.realtime
def test_realtime_send_and_buffer_swaps():
    """Host.send from the audio thread while Python swaps the buffer it plays."""
    import threading
    import time

    from numchuck import _numchuck

    c = Chuck(sample_rate=44100, input_channels=0, output_channels=2)
    threads = set()
    count = [0]

    def callback(name, value):
        threads.add(threading.get_ident())
        count[0] += 1

    c.on_msg(callback)
    c.on_receive("bang", lambda value: callback("bang", 0))
    c.compile("""
        HostBufPlay p => dac; p.name("noise"); 1 => p.loop; 0.1 => p.gain;
        while (true) {
            Host.msg("tick", now / samp); Host.sendBang("bang"); 10::ms => now;
        }
    """)
    assert _numchuck.start_audio(c.raw, sample_rate=44100, num_dac_channels=2)
    try:
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            c.set_buffer("noise", np.random.uniform(-1, 1, 512).astype(np.float32))
            c.remove_buffer("noise")
    finally:
        _numchuck.stop_audio()
        _numchuck.shutdown_audio()
        c.close()
    assert count[0] > 20
    assert threading.get_ident() not in threads
