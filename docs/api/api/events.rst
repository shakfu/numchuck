Event System
============

Global event communication between Python and ChucK.

Overview
--------

The event system allows bidirectional communication through ChucK global events:

* **Python → ChucK**: Signal or broadcast events from Python
* **ChucK → Python**: Listen for events and execute Python callbacks
* **Multiple listeners**: Multiple Python callbacks can listen to the same event

Event Methods
-------------

From ChucK Class
~~~~~~~~~~~~~~~~

.. automethod:: pychuck.ChucK.signal_global_event

.. automethod:: pychuck.ChucK.broadcast_global_event

.. automethod:: pychuck.ChucK.listen_for_global_event

.. automethod:: pychuck.ChucK.stop_listening_for_global_event

Usage Examples
--------------

Define Event in ChucK
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chuck.compile_code('''
       global Event trigger;
   ''')

Signal from Python
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Wake one waiting shred
   chuck.signal_global_event("trigger")

   # Wake all waiting shreds
   chuck.broadcast_global_event("trigger")

Listen from Python
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def on_trigger():
       print("Event triggered!")

   # Listen once
   listener_id = chuck.listen_for_global_event(
       "trigger", on_trigger, listen_forever=False
   )

   # Listen forever
   listener_id = chuck.listen_for_global_event(
       "trigger", on_trigger, listen_forever=True
   )

Stop Listening
~~~~~~~~~~~~~~

.. code-block:: python

   # Always clean up listeners to prevent memory leaks
   chuck.stop_listening_for_global_event("trigger", listener_id)

Complete Example
----------------

Beat Synchronization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pychuck
   import time

   chuck = pychuck.ChucK()
   chuck.set_param(pychuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(pychuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(pychuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # ChucK generates beats
   chuck.compile_code('''
       global Event beat;
       global int beat_number;

       while(true) {
           beat_number++;
           beat.broadcast();
           500::ms => now;
       }
   ''')

   # Python responds
   def on_beat():
       print(f"Beat!")

   listener_id = chuck.listen_for_global_event("beat", on_beat)

   time.sleep(5)

   chuck.stop_listening_for_global_event("beat", listener_id)
   chuck.remove_all_shreds()

Trigger Synthesis
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Python triggers notes in ChucK
   chuck.compile_code('''
       global Event note_on;
       global float frequency;

       while(true) {
           note_on => now;

           SinOsc s => ADSR env => dac;
           env.set(10::ms, 50::ms, 0.5, 100::ms);

           frequency => s.freq;
           0.5 => s.gain;

           env.keyOn();
           200::ms => now;
           env.keyOff();
           100::ms => now;
       }
   ''')

   # Trigger from Python
   notes = [261.63, 293.66, 329.63, 392.00]
   for freq in notes:
       chuck.set_global_float("frequency", freq)
       chuck.signal_global_event("note_on")
       time.sleep(0.3)

Memory Management
-----------------

**Important**: Always stop listening to prevent memory leaks:

.. code-block:: python

   # Register listener
   listener_id = chuck.listen_for_global_event("event", callback)

   # Use it...

   # ALWAYS clean up
   chuck.stop_listening_for_global_event("event", listener_id)

Context Manager Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class EventListener:
       def __init__(self, chuck, event_name, callback):
           self.chuck = chuck
           self.event_name = event_name
           self.callback = callback
           self.listener_id = None

       def __enter__(self):
           self.listener_id = self.chuck.listen_for_global_event(
               self.event_name, self.callback
           )
           return self

       def __exit__(self, exc_type, exc_val, exc_tb):
           if self.listener_id:
               self.chuck.stop_listening_for_global_event(
                   self.event_name, self.listener_id
               )
           return False

   # Usage
   with EventListener(chuck, "trigger", on_trigger):
       # Automatic cleanup
       time.sleep(5)

See Also
--------

* :doc:`chuck` - ChucK class reference
* :doc:`../error_handling` - Error handling guide
* :doc:`../examples` - More examples
