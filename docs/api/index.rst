pychuck API Reference
=====================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   api/chuck
   api/audio
   api/events
   api/constants
   error_handling
   examples

Introduction
------------

pychuck provides Python bindings for the ChucK audio programming language,
enabling real-time audio synthesis, live coding, and programmatic control
of ChucK from Python.

Quick Start
-----------

.. code-block:: python

   import pychuck

   # Create and initialize ChucK instance
   chuck = pychuck.ChucK()
   chuck.init(44100, 2)

   # Compile and run ChucK code
   success, shred_ids = chuck.compile_code('''
       SinOsc s => dac;
       440 => s.freq;
       1::second => now;
   ''')

   if success:
       print(f"Running shreds: {shred_ids}")

Installation
------------

.. code-block:: bash

   pip install pychuck

Or from source:

.. code-block:: bash

   git clone --recursive https://github.com/shakfu/pychuck
   cd pychuck
   pip install -e .

Key Features
------------

* **Complete ChucK API Access**: Compilation, VM control, audio processing
* **Real-time Audio**: Integration with system audio via RtAudio
* **Global Variables**: Bidirectional communication with ChucK VM
* **Event System**: Listen for and trigger ChucK events from Python
* **Shred Management**: Live coding with hot-swapping support
* **TUI Applications**: Interactive REPL and multi-tab editor

API Overview
------------

Main Classes
~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary
   :recursive:

   pychuck.ChucK

Core Functions
~~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary

   pychuck.version
   pychuck.start_audio
   pychuck.stop_audio
   pychuck.shutdown_audio
   pychuck.audio_info

Error Handling
--------------

pychuck uses exception-based error handling:

* ``ValueError``: Invalid input parameters
* ``RuntimeError``: Operational failures
* Compilation errors return ``(False, [])`` tuple

See :doc:`error_handling` for complete guide.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
