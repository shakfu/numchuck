Examples
========

Complete examples demonstrating common numchuck usage patterns.

Basic Synthesis
---------------

Simple Sine Wave
~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Simple 440Hz sine wave
   code = '''
       SinOsc s => dac;
       440 => s.freq;
       0.3 => s.gain;
       while(true) { 100::ms => now; }
   '''

   success, shred_ids = chuck.compile_code(code)
   if success:
       time.sleep(2)  # Play for 2 seconds
       chuck.remove_shred(shred_ids[0])

Chord Generator
~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Generate a major chord
   frequencies = [261.63, 329.63, 392.00]  # C major (C4, E4, G4)

   for i, freq in enumerate(frequencies):
       code = f'''
           SinOsc s => dac;
           {freq} => s.freq;
           0.2 => s.gain;
           while(true) {{ 100::ms => now; }}
       '''
       chuck.compile_code(code)

   time.sleep(3)
   chuck.remove_all_shreds()

Live Coding
-----------

Interactive Parameter Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Define global frequency variable
   chuck.compile_code('''
       global float freq;
       SinOsc s => dac;
       0.3 => s.gain;

       while(true) {
           freq => s.freq;
           10::ms => now;
       }
   ''')

   # Control frequency from Python
   for freq in [220, 440, 880, 440]:
       chuck.set_global_float("freq", freq)
       time.sleep(0.5)

   chuck.remove_all_shreds()

Hot-Swapping Shreds
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Initial pattern
   code1 = '''
       SinOsc s => dac;
       while(true) {
           440 => s.freq;
           100::ms => now;
           550 => s.freq;
           100::ms => now;
       }
   '''

   success, shred_ids = chuck.compile_code(code1)
   shred_id = shred_ids[0]

   time.sleep(1)

   # Replace with new pattern (no gap in audio)
   code2 = '''
       SawOsc s => dac;
       while(true) {
           220 => s.freq;
           200::ms => now;
       }
   '''

   new_id = chuck.replace_shred(shred_id, code2)
   time.sleep(1)

   chuck.remove_shred(new_id)

Event-Driven Control
--------------------

Trigger Synthesis
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Define event-triggered synthesis
   chuck.compile_code('''
       global Event bang;
       global float freq;

       while(true) {
           bang => now;

           SinOsc s => ADSR env => dac;
           env.set(10::ms, 50::ms, 0.5, 200::ms);

           freq => s.freq;
           0.5 => s.gain;
           env.keyOn();
           250::ms => now;
           env.keyOff();
           200::ms => now;
       }
   ''')

   # Trigger notes from Python
   notes = [261.63, 293.66, 329.63, 349.23, 392.00]  # C major scale
   for freq in notes:
       chuck.set_global_float("freq", freq)
       chuck.signal_global_event("bang")
       time.sleep(0.3)

   chuck.remove_all_shreds()

Bidirectional Communication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # ChucK reports beat events
   chuck.compile_code('''
       global Event beat;
       global int beat_count;

       while(true) {
           beat_count++;
           beat.broadcast();
           500::ms => now;
       }
   ''')

   # Python responds to beats
   def on_beat():
       result = [0]
       def get_count(val):
           result[0] = val
       chuck.get_global_int("beat_count", get_count)
       time.sleep(0.01)
       print(f"Beat {result[0]}")

   listener_id = chuck.listen_for_global_event("beat", on_beat)

   time.sleep(5)

   chuck.stop_listening_for_global_event("beat", listener_id)
   chuck.remove_all_shreds()

Audio Processing
----------------

Offline Rendering
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import numpy as np
   import wave

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()

   # Generate audio
   chuck.compile_code('''
       SinOsc s => dac;
       440 => s.freq;
       0.5 => s.gain;
       while(true) { 1::samp => now; }
   ''')

   # Render 3 seconds to buffer
   sample_rate = 44100
   duration = 3.0
   frames = int(sample_rate * duration)
   channels = 2

   input_buf = np.zeros(frames * 0, dtype=np.float32)
   output_buf = np.zeros(frames * channels, dtype=np.float32)

   chuck.run(input_buf, output_buf, frames)

   # Save to WAV file
   output_buf = (output_buf * 32767).astype(np.int16)
   with wave.open('output.wav', 'w') as wav:
       wav.setnchannels(channels)
       wav.setsampwidth(2)
       wav.setframerate(sample_rate)
       wav.writeframes(output_buf.tobytes())

Real-time Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import numpy as np
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()

   # Generate modulating sine wave
   chuck.compile_code('''
       SinOsc s => dac;
       SinOsc lfo => blackhole;

       0.5 => lfo.freq;

       while(true) {
           200 + (lfo.last() * 200) => s.freq;
           0.3 => s.gain;
           1::ms => now;
       }
   ''')

   # Analyze output in real-time
   frames = 1024
   input_buf = np.zeros(frames * 0, dtype=np.float32)
   output_buf = np.zeros(frames * 2, dtype=np.float32)

   for _ in range(50):
       chuck.run(input_buf, output_buf, frames)

       # Calculate RMS level
       rms = np.sqrt(np.mean(output_buf ** 2))
       print(f"RMS: {rms:.4f}")

       time.sleep(0.1)

   chuck.remove_all_shreds()

File-Based Workflows
--------------------

Load and Run ChucK Files
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Compile from file
   success, shred_ids = chuck.compile_file('melody.ck')
   if success:
       print(f"Loaded {len(shred_ids)} shreds")

   time.sleep(5)
   chuck.remove_all_shreds()

Multiple File Compilation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Load multiple files
   files = ['bass.ck', 'drums.ck', 'melody.ck']
   for filename in files:
       success, shred_ids = chuck.compile_file(filename)
       if success:
           print(f"Loaded {filename}: shred {shred_ids[0]}")

   time.sleep(10)
   chuck.remove_all_shreds()

Advanced Patterns
-----------------

Sequencer
~~~~~~~~~

.. code-block:: python

   import numchuck
   import time

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Define sequencer in ChucK
   chuck.compile_code('''
       global Event trigger;
       global float freq;

       while(true) {
           trigger => now;

           SinOsc s => ADSR env => dac;
           env.set(5::ms, 50::ms, 0.3, 100::ms);

           freq => s.freq;
           0.4 => s.gain;
           env.keyOn();
           80::ms => now;
           env.keyOff();
           20::ms => now;
       }
   ''')

   # Python sequence
   sequence = [
       (261.63, 0.2),  # C4
       (293.66, 0.2),  # D4
       (329.63, 0.2),  # E4
       (349.23, 0.2),  # F4
       (392.00, 0.4),  # G4
       (349.23, 0.2),  # F4
       (329.63, 0.4),  # E4
       (261.63, 0.4),  # C4
   ]

   for _ in range(3):  # Play 3 times
       for freq, duration in sequence:
           chuck.set_global_float("freq", freq)
           chuck.signal_global_event("trigger")
           time.sleep(duration)

   chuck.remove_all_shreds()

Multiple Instances
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   # Create two separate ChucK instances
   chuck1 = numchuck.ChucK()
   chuck1.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck1.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck1.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck1.init()

   chuck2 = numchuck.ChucK()
   chuck2.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck2.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck2.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck2.init()

   # Each instance can run independently
   chuck1.compile_code('SinOsc s => dac; 220 => s.freq; while(true) { 100::ms => now; }')
   chuck2.compile_code('SawOsc s => dac; 440 => s.freq; while(true) { 100::ms => now; }')

See Also
--------

* :doc:`quickstart` - Getting started
* :doc:`api/chuck` - Complete API reference
* :doc:`error_handling` - Error handling guide
