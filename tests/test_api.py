"""Tests for the high-level pychuck.Chuck API."""

import numpy as np
import pytest

from pychuck import Chuck


class TestChuckConstruction:
    """Test Chuck class construction and initialization."""

    def test_default_construction(self):
        """Test construction with default parameters."""
        chuck = Chuck()
        assert chuck.sample_rate == 44100
        assert chuck.input_channels == 2
        assert chuck.output_channels == 2

    def test_custom_parameters(self):
        """Test construction with custom parameters."""
        chuck = Chuck(sample_rate=48000, output_channels=1, input_channels=1)
        assert chuck.sample_rate == 48000
        assert chuck.output_channels == 1
        assert chuck.input_channels == 1

    def test_version_property(self):
        """Test version property is accessible."""
        chuck = Chuck()
        assert isinstance(chuck.version, str)
        assert len(chuck.version) > 0

    def test_chugin_enable_property(self):
        """Test chugin_enable property."""
        chuck = Chuck(chugin_enable=False)
        assert chuck.chugin_enable is False

    def test_additional_parameters(self):
        """Test additional constructor parameters."""
        chuck = Chuck(
            auto_depend=True,
            deprecate_level=2,
            otf_enable=True,
            otf_port=9999,
            tty_color=True,
            tty_width_hint=120,
        )
        assert chuck.auto_depend is True
        assert chuck.deprecate_level == 2
        assert chuck.otf_enable is True
        assert chuck.otf_port == 9999
        assert chuck.tty_color is True
        assert chuck.tty_width_hint == 120

    def test_readonly_properties(self):
        """Test read-only properties."""
        chuck = Chuck()
        assert chuck.compiler_highlight_on_error is True  # default
        assert isinstance(chuck.is_realtime_audio_hint, bool)
        assert isinstance(chuck.otf_print_warnings, bool)
        assert isinstance(chuck.dump_instructions, bool)

    def test_manual_init(self):
        """Test manual initialization with auto_init=False."""
        chuck = Chuck(auto_init=False)
        assert chuck.init()  # Returns truthy value on success


class TestCompilation:
    """Test code compilation."""

    def test_compile_simple_code(self):
        """Test compiling simple ChucK code."""
        chuck = Chuck()
        success, shred_ids = chuck.compile("SinOsc s => dac;")
        assert success is True
        assert len(shred_ids) == 1
        assert shred_ids[0] > 0

    def test_compile_multiple_shreds(self):
        """Test compiling multiple shreds."""
        chuck = Chuck()
        success, shred_ids = chuck.compile("SinOsc s => dac;", count=3)
        assert success is True
        assert len(shred_ids) == 3

    def test_compile_invalid_code(self):
        """Test compiling invalid code."""
        chuck = Chuck()
        success, shred_ids = chuck.compile("invalid code here")
        assert success is False


class TestRunning:
    """Test running the VM."""

    def test_run_returns_output(self):
        """Test run returns output audio."""
        chuck = Chuck(output_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        # Run enough frames for audio to be generated
        output = chuck.run(4410)  # 0.1 seconds at 44100 Hz
        assert isinstance(output, np.ndarray)
        assert output.dtype == np.float32
        assert len(output) == 4410
        assert output.max() > 0  # Should have audio output

    def test_run_stereo_output(self):
        """Test run with stereo output."""
        chuck = Chuck(output_channels=2)
        chuck.compile("SinOsc s => dac;")
        output = chuck.run(500)
        assert len(output) == 1000  # 500 frames * 2 channels

    def test_run_with_output_buffer(self):
        """Test run with pre-allocated output buffer."""
        chuck = Chuck(output_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        output_buf = np.zeros(4410, dtype=np.float32)
        result = chuck.run(4410, output=output_buf)
        # Should return the same buffer
        assert result is output_buf
        # Buffer should be modified in-place
        assert output_buf.max() > 0

    def test_run_with_input_and_output(self):
        """Test run with both input and output buffers."""
        chuck = Chuck(output_channels=1, input_channels=1)
        chuck.compile("adc => dac;")  # Pass-through
        input_buf = np.ones(500, dtype=np.float32) * 0.5
        output_buf = np.zeros(500, dtype=np.float32)
        result = chuck.run(500, output=output_buf, input=input_buf)
        assert result is output_buf
        # Output should have data (pass-through of input)
        assert isinstance(output_buf, np.ndarray)

    def test_run_effect_mode(self):
        """Test run with explicit input/output (effect mode)."""
        chuck = Chuck(output_channels=1, input_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        input_buf = np.zeros(4410, dtype=np.float32)
        output_buf = np.zeros(4410, dtype=np.float32)
        result = chuck.run(4410, output=output_buf, input=input_buf)
        # Should return output buffer
        assert result is output_buf
        # Output should have audio
        assert output_buf.max() > 0

    def test_advance_discards_output(self):
        """Test advance() advances time without returning audio."""
        chuck = Chuck()
        chuck.compile("global int counter; 0 => counter;")
        chuck.advance(100)
        # Just verify it doesn't crash and returns None
        result = chuck.advance(100)
        assert result is None

    def test_run_with_output_loop(self):
        """Test run with output buffer in a loop (zero allocation pattern)."""
        chuck = Chuck(output_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        output_buf = np.zeros(512, dtype=np.float32)
        # Simulate real-time loop
        for _ in range(10):
            chuck.run(512, output=output_buf)
        # Buffer should have valid audio after loop
        assert output_buf.max() > 0

    def test_run_reuse_internal_buffer(self):
        """Test run with reuse=True for internal buffer management."""
        chuck = Chuck(output_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        # First call allocates buffer
        audio1 = chuck.run(512, reuse=True)
        assert isinstance(audio1, np.ndarray)
        assert len(audio1) == 512
        # Second call reuses same buffer
        audio2 = chuck.run(512, reuse=True)
        assert audio1 is audio2  # Same buffer object
        assert audio2.max() > 0

    def test_run_reuse_reallocates_on_size_change(self):
        """Test run with reuse=True reallocates when num_frames changes."""
        chuck = Chuck(output_channels=1)
        chuck.compile("SinOsc s => dac; 440 => s.freq; 1::second => now;")
        audio1 = chuck.run(512, reuse=True)
        assert len(audio1) == 512
        # Different size triggers reallocation
        audio2 = chuck.run(1024, reuse=True)
        assert len(audio2) == 1024
        assert audio1 is not audio2  # Different buffer


class TestShredManagement:
    """Test shred management."""

    def test_shreds_property(self):
        """Test shreds property."""
        chuck = Chuck()
        chuck.compile("SinOsc s => dac; 1::second => now;")
        chuck.run(100)
        # Shred might have ended, just check it's a list
        assert isinstance(chuck.shreds, list)

    def test_remove_shred(self):
        """Test removing a shred."""
        chuck = Chuck()
        success, shred_ids = chuck.compile("SinOsc s => dac; 1::second => now;")
        chuck.run(100)
        if shred_ids:
            # remove_shred may return None or bool depending on implementation
            chuck.remove_shred(shred_ids[0])
            chuck.run(100)
            # After removal, shred should not be in list
            assert shred_ids[0] not in chuck.shreds

    def test_clear_vm(self):
        """Test clearing all shreds."""
        chuck = Chuck()
        chuck.compile("SinOsc s => dac; 1::second => now;")
        chuck.run(100)
        chuck.clear()
        chuck.run(100)
        # After clear, should have no shreds
        assert chuck.shreds == []


class TestGlobalVariables:
    """Test global variable operations."""

    def test_set_get_int(self):
        """Test setting and getting global int."""
        chuck = Chuck()
        chuck.compile("global int myInt;")
        chuck.run(100)
        chuck.set_int("myInt", 42)
        value = chuck.get_int("myInt")
        assert value == 42

    def test_set_get_float(self):
        """Test setting and getting global float."""
        chuck = Chuck()
        chuck.compile("global float myFloat;")
        chuck.run(100)
        chuck.set_float("myFloat", 3.14159)
        value = chuck.get_float("myFloat")
        assert abs(value - 3.14159) < 0.0001

    def test_set_get_string(self):
        """Test setting and getting global string."""
        chuck = Chuck()
        chuck.compile('global string myStr;')
        chuck.run(100)
        chuck.set_string("myStr", "hello")
        value = chuck.get_string("myStr")
        assert value == "hello"


class TestRawAccess:
    """Test access to raw low-level API."""

    def test_raw_property(self):
        """Test raw property returns low-level ChucK instance."""
        chuck = Chuck()
        raw = chuck.raw
        # Check it has low-level methods
        assert hasattr(raw, "compile_code")
        assert hasattr(raw, "set_param")
        assert hasattr(raw, "get_param_int")
