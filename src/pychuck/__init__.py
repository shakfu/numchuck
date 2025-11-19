"""
pychuck: Python bindings for ChucK audio programming language

This module provides comprehensive Python bindings for the ChucK audio
programming language, enabling real-time audio synthesis, live coding,
and programmatic control of ChucK from Python.

Error Handling:
    All ChucK operations that can fail will raise exceptions:
    - ValueError: Invalid input parameters (empty strings, zero/negative values)
    - RuntimeError: ChucK not initialized or operation failed
    - TypeError: Incorrect type passed to function

Examples:
    >>> import pychuck
    >>> chuck = pychuck.ChucK()
    >>> chuck.init(44100, 2)  # Returns True on success, raises on error
    >>> result, shred_ids = chuck.compile_code("SinOsc s => dac;")
    >>> if result:
    ...     print(f"Compiled successfully: {shred_ids}")
"""

from ._version import __version__, __version_info__

from ._pychuck import (
    ChucK,
    version,
    __doc__,
    # Parameter constants
    PARAM_AUTO_DEPEND,
    PARAM_CHUGIN_ENABLE,
    PARAM_DEPRECATE_LEVEL,
    PARAM_DUMP_INSTRUCTIONS,
    PARAM_INPUT_CHANNELS,
    PARAM_OTF_ENABLE,
    PARAM_OTF_PORT,
    PARAM_OUTPUT_CHANNELS,
    PARAM_SAMPLE_RATE,
    PARAM_USER_CHUGINS,
    PARAM_VERSION,
    PARAM_VM_ADAPTIVE,
    PARAM_VM_HALT,
    PARAM_WORKING_DIRECTORY,
    # Log level constants
    LOG_NONE,
    LOG_CORE,
    LOG_SYSTEM,
    LOG_HERALD,
    LOG_WARNING,
    LOG_INFO,
    LOG_DEBUG,
    LOG_FINE,
    LOG_FINER,
    LOG_FINEST,
    LOG_ALL,
    # Real-time audio functions
    start_audio,
    stop_audio,
    shutdown_audio,
    audio_info,
)

__all__ = [
    "ChucK",
    "version",
    "PARAM_AUTO_DEPEND",
    "PARAM_CHUGIN_ENABLE",
    "PARAM_DEPRECATE_LEVEL",
    "PARAM_DUMP_INSTRUCTIONS",
    "PARAM_INPUT_CHANNELS",
    "PARAM_OTF_ENABLE",
    "PARAM_OTF_PORT",
    "PARAM_OUTPUT_CHANNELS",
    "PARAM_SAMPLE_RATE",
    "PARAM_USER_CHUGINS",
    "PARAM_VERSION",
    "PARAM_VM_ADAPTIVE",
    "PARAM_VM_HALT",
    "PARAM_WORKING_DIRECTORY",
    "LOG_NONE",
    "LOG_CORE",
    "LOG_SYSTEM",
    "LOG_HERALD",
    "LOG_WARNING",
    "LOG_INFO",
    "LOG_DEBUG",
    "LOG_FINE",
    "LOG_FINER",
    "LOG_FINEST",
    "LOG_ALL",
    "start_audio",
    "stop_audio",
    "shutdown_audio",
    "audio_info",
]
