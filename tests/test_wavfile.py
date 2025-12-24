"""Tests for WAV file rendering using ChucK's native WvOut."""

import os
import tempfile

import pytest

from numchuck import Chuck


class TestWvOut:
    """Test ChucK's native WvOut for WAV file writing."""

    def test_render_sine_to_wav(self):
        """Test rendering a sine wave to a WAV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sine_output.wav")

            chuck = Chuck(sample_rate=44100, output_channels=2)

            # ChucK code that records to WAV using WvOut
            code = f'''
            SinOsc s => dac;
            440 => s.freq;
            0.5 => s.gain;

            s => WvOut w => blackhole;
            "{output_path}" => w.wavFilename;

            1 => w.record;
            1::second => now;
            0 => w.record;
            w.closeFile();
            '''

            success, shred_ids = chuck.compile(code)
            assert success, "Failed to compile WvOut code"
            assert len(shred_ids) == 1

            # Run for 1 second of audio
            chuck.run(44100)

            # Verify WAV file was created
            assert os.path.exists(output_path), "WAV file was not created"
            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"WAV file too small: {file_size} bytes"

    def test_render_stereo_to_wav(self):
        """Test rendering stereo audio to a WAV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "stereo_output.wav")

            chuck = Chuck(sample_rate=44100, output_channels=2)

            # Stereo recording from dac
            code = f'''
            SinOsc left => dac.left;
            SinOsc right => dac.right;
            440 => left.freq;
            550 => right.freq;
            0.5 => left.gain;
            0.5 => right.gain;

            dac => WvOut w => blackhole;
            "{output_path}" => w.wavFilename;

            1 => w.record;
            1::second => now;
            0 => w.record;
            w.closeFile();
            '''

            success, shred_ids = chuck.compile(code)
            assert success, "Failed to compile stereo WvOut code"

            chuck.run(44100)

            assert os.path.exists(output_path), "Stereo WAV file was not created"
            file_size = os.path.getsize(output_path)
            # Stereo file should be larger
            assert file_size > 2000, f"Stereo WAV file too small: {file_size} bytes"

    def test_render_example_file(self):
        """Test rendering an example ChucK file to WAV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "example_output.wav")

            chuck = Chuck(sample_rate=44100, output_channels=2)

            # Load and compile the example file
            example_path = os.path.join(
                os.path.dirname(__file__), "..", "examples", "basic", "foo.ck"
            )
            with open(example_path, "r") as f:
                example_code = f.read()

            success, shred_ids = chuck.compile(example_code)
            assert success, "Failed to compile foo.ck"

            # Add recording shred
            record_code = f'''
            dac => WvOut w => blackhole;
            "{output_path}" => w.wavFilename;

            1 => w.record;
            3::second => now;
            0 => w.record;
            w.closeFile();
            '''

            success, rec_ids = chuck.compile(record_code)
            assert success, "Failed to compile recording shred"

            # Run for 3 seconds
            chuck.run(44100 * 3)

            assert os.path.exists(output_path), "Example WAV file was not created"
            file_size = os.path.getsize(output_path)
            # 3 seconds of stereo 16-bit audio ~ 529KB
            assert file_size > 100000, f"Example WAV file too small: {file_size} bytes"

    def test_me_dir_path(self):
        """Test using me.dir() style path construction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "medir_output.wav")

            chuck = Chuck(sample_rate=44100, output_channels=2, working_directory=tmpdir)

            code = '''
            SinOsc s => dac;
            440 => s.freq;

            s => WvOut w => blackhole;
            me.dir() + "/medir_output.wav" => w.wavFilename;

            1 => w.record;
            0.5::second => now;
            0 => w.record;
            w.closeFile();
            '''

            success, shred_ids = chuck.compile(code)
            assert success, "Failed to compile me.dir() code"

            chuck.run(22050)  # 0.5 seconds

            assert os.path.exists(output_path), "me.dir() WAV file was not created"
