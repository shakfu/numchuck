Quick Start Guide
=================

This guide will help you get started with numchuck quickly.

Installation
------------

From PyPI (when available):

.. code-block:: bash

   pip install numchuck

From source:

.. code-block:: bash

   git clone --recursive https://github.com/shakfu/numchuck
   cd numchuck
   pip install -e .

Basic Usage
-----------

Initialize ChucK
~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   # Create ChucK instance
   chuck = numchuck.ChucK()

   # Configure audio parameters
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)

   # Initialize and start
   chuck.init()
   chuck.start()

Compile and Run Code
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Simple sine wave
   code = '''
       SinOsc s => dac;
       440 => s.freq;
       0.5 => s.gain;
       while(true) { 100::ms => now; }
   '''

   success, shred_ids = chuck.compile_code(code)
   if success:
       print(f"Shred {shred_ids[0]} is running!")

Shred Management
~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all running shreds
   all_shreds = chuck.get_all_shred_ids()

   # Get shred information
   info = chuck.get_shred_info(shred_ids[0])
   print(f"Shred {info['id']}: {info['name']}")

   # Remove a shred
   chuck.remove_shred(shred_ids[0])

   # Remove all shreds
   chuck.remove_all_shreds()

Global Variables
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Define global variables in ChucK
   chuck.compile_code('''
       global int counter;
       global float frequency;
   ''')

   # Set from Python
   chuck.set_global_int("counter", 42)
   chuck.set_global_float("frequency", 440.0)

   # Get from ChucK (async)
   def on_counter(value):
       print(f"Counter: {value}")

   chuck.get_global_int("counter", on_counter)

Events
~~~~~~

.. code-block:: python

   # Define event in ChucK
   chuck.compile_code('global Event trigger;')

   # Listen for event
   def on_trigger():
       print("Event triggered!")

   listener_id = chuck.listen_for_global_event("trigger", on_trigger)

   # Signal event from Python
   chuck.signal_global_event("trigger")

   # Clean up listener
   chuck.stop_listening_for_global_event("trigger", listener_id)

Offline Rendering
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numpy as np

   # Compile audio code
   chuck.compile_code('''
       SinOsc s => dac;
       440 => s.freq;
       while(true) { 1::samp => now; }
   ''')

   # Render to buffer
   frames = 44100  # 1 second
   input_buf = np.zeros(frames * 0, dtype=np.float32)
   output_buf = np.zeros(frames * 2, dtype=np.float32)

   chuck.run(input_buf, output_buf, frames)

   # output_buf now contains rendered audio

Command-Line Tools
------------------

Interactive REPL
~~~~~~~~~~~~~~~~

.. code-block:: bash

   numchuck repl

   # Or with files
   numchuck repl file1.ck file2.ck

   # With project versioning
   numchuck repl --project my-project

Multi-Tab Editor
~~~~~~~~~~~~~~~~

.. code-block:: bash

   numchuck edit

   # Or open files
   numchuck edit file1.ck file2.ck

   # With project versioning
   numchuck edit --project live-session

Run Files
~~~~~~~~~

.. code-block:: bash

   # Execute ChucK files
   numchuck run file1.ck file2.ck

   # With custom settings
   numchuck run file.ck --srate 48000 --channels 2

   # Run for specific duration
   numchuck run file.ck --duration 10

Version Info
~~~~~~~~~~~~

.. code-block:: bash

   numchuck version  # Show numchuck and ChucK versions
   numchuck info     # Show detailed system info

Next Steps
----------

* Read the :doc:`api/chuck` for complete API reference
* Check :doc:`error_handling` for error handling guide
* Browse :doc:`examples` for more code samples
* Try the interactive REPL: ``numchuck repl``
