"""
Tests for shared TUI utilities in common.py.

Tests the helper functions used for shreds table formatting.
"""

import pytest
from numchuck.tui.common import format_elapsed_time, format_shred_name, generate_shreds_table


class TestFormatElapsedTime:
    """Tests for format_elapsed_time function."""

    def test_seconds_only(self):
        """Test formatting under 60 seconds."""
        assert format_elapsed_time(0.0) == "0.0s"
        assert format_elapsed_time(5.5) == "5.5s"
        assert format_elapsed_time(59.9) == "59.9s"

    def test_minutes_and_seconds(self):
        """Test formatting between 1 minute and 1 hour."""
        assert format_elapsed_time(60.0) == "1m00.0s"
        assert format_elapsed_time(90.5) == "1m30.5s"
        assert format_elapsed_time(3599.9) == "59m59.9s"

    def test_hours_and_minutes(self):
        """Test formatting over 1 hour."""
        assert format_elapsed_time(3600.0) == "1h00m"
        assert format_elapsed_time(3660.0) == "1h01m"
        assert format_elapsed_time(7200.0) == "2h00m"
        assert format_elapsed_time(7380.0) == "2h03m"


class TestFormatShredName:
    """Tests for format_shred_name function."""

    def test_simple_filename(self):
        """Test simple filename."""
        assert format_shred_name("test.ck") == "test.ck"

    def test_path_with_parent(self):
        """Test path shows parent/filename."""
        assert format_shred_name("/path/to/test.ck") == "to/test.ck"

    def test_path_just_filename(self):
        """Test path with no parent directory."""
        assert format_shred_name("/test.ck") == "test.ck"

    def test_truncation(self):
        """Test long names are truncated."""
        long_name = "a" * 100 + ".ck"
        result = format_shred_name(long_name)
        assert len(result) == 56

    def test_custom_max_len(self):
        """Test custom max length."""
        result = format_shred_name("verylongfilename.ck", max_len=10)
        assert len(result) == 10

    def test_non_path_string(self):
        """Test non-path strings handled gracefully."""
        assert format_shred_name("inline code") == "inline code"


class TestGenerateShedsTable:
    """Tests for generate_shreds_table function."""

    def test_empty_shreds(self):
        """Test with no shreds returns message."""
        result = generate_shreds_table({}, None)
        assert result == "No active shreds"

    def test_with_pipes(self):
        """Test table with pipe separators."""

        class MockChuck:
            def now(self):
                return 44100.0  # 1 second

            def get_param_int(self, param):
                return 44100

        shreds = {
            1: {"name": "test.ck", "time": 0.0},
        }
        result = generate_shreds_table(shreds, MockChuck(), use_pipes=True)
        assert "|" in result
        assert "ID" in result
        assert "Name" in result
        assert "Elapsed" in result
        assert "test.ck" in result
        assert "1.0s" in result

    def test_without_pipes(self):
        """Test table without pipe separators (spaces only)."""

        class MockChuck:
            def now(self):
                return 44100.0

            def get_param_int(self, param):
                return 44100

        shreds = {
            1: {"name": "test.ck", "time": 0.0},
        }
        result = generate_shreds_table(shreds, MockChuck(), use_pipes=False)
        assert "|" not in result
        # Uses Unicode box drawing character
        assert "\u2500" in result

    def test_multiple_shreds(self):
        """Test with multiple shreds."""

        class MockChuck:
            def now(self):
                return 88200.0  # 2 seconds

            def get_param_int(self, param):
                return 44100

        shreds = {
            1: {"name": "first.ck", "time": 0.0},
            2: {"name": "second.ck", "time": 44100.0},
        }
        result = generate_shreds_table(shreds, MockChuck(), use_pipes=True)
        assert "first.ck" in result
        assert "second.ck" in result
        # First shred: 2 seconds elapsed
        assert "2.0s" in result
        # Second shred: 1 second elapsed
        assert "1.0s" in result

    def test_chuck_error_handling(self):
        """Test graceful handling when ChucK raises errors."""

        class BrokenChuck:
            def now(self):
                raise RuntimeError("ChucK not initialized")

            def get_param_int(self, param):
                raise RuntimeError("ChucK not initialized")

        shreds = {
            1: {"name": "test.ck", "time": 0.0},
        }
        # Should not raise, should use defaults
        result = generate_shreds_table(shreds, BrokenChuck(), use_pipes=True)
        assert "test.ck" in result
        assert "0.0s" in result

    def test_shreds_sorted_by_id(self):
        """Test shreds are sorted by ID."""

        class MockChuck:
            def now(self):
                return 0.0

            def get_param_int(self, param):
                return 44100

        shreds = {
            3: {"name": "third.ck", "time": 0.0},
            1: {"name": "first.ck", "time": 0.0},
            2: {"name": "second.ck", "time": 0.0},
        }
        result = generate_shreds_table(shreds, MockChuck(), use_pipes=True)
        lines = result.split("\n")
        # Header + separator + 3 shreds = 5 lines
        assert len(lines) == 5
        # Check order (skip header and separator)
        assert "1" in lines[2] and "first.ck" in lines[2]
        assert "2" in lines[3] and "second.ck" in lines[3]
        assert "3" in lines[4] and "third.ck" in lines[4]
