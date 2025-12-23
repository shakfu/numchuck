Error Handling
==============

numchuck uses exception-based error handling for a clean and Pythonic API.

Exception Types
---------------

ValueError
~~~~~~~~~~

Raised when invalid input parameters are provided:

* Empty strings where content is required
* Zero or negative values for sizes/counts
* Invalid parameter values

**Example:**

.. code-block:: python

   chuck = numchuck.ChucK()

   # ValueError: Sample rate must be positive
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, -1)

   # ValueError: Code cannot be empty
   chuck.compile_code("")

RuntimeError
~~~~~~~~~~~~

Raised when operations fail or ChucK is not properly initialized:

* ChucK VM not initialized
* Compilation failures (when operation itself fails, not syntax errors)
* Audio system failures

**Example:**

.. code-block:: python

   chuck = numchuck.ChucK()

   # RuntimeError: ChucK not initialized
   chuck.compile_code("SinOsc s => dac;")

   # Proper usage:
   chuck.init()
   chuck.compile_code("SinOsc s => dac;")  # OK

TypeError
~~~~~~~~~

Raised when incorrect types are passed:

* Wrong buffer types for audio processing
* Incorrect callback signatures

**Example:**

.. code-block:: python

   # TypeError: Expected numpy array
   chuck.run([0, 1, 2], output, frames)

Compilation Errors
------------------

Compilation errors (syntax errors, type mismatches) return ``(False, [])``
instead of raising exceptions, since they're expected during development:

.. code-block:: python

   # Syntax error - returns (False, [])
   success, shred_ids = chuck.compile_code("invalid syntax!")
   if not success:
       print("Compilation failed")

   # Successful compilation - returns (True, [shred_id])
   success, shred_ids = chuck.compile_code("SinOsc s => dac;")
   if success:
       print(f"Running: {shred_ids}")

Best Practices
--------------

Always Initialize
~~~~~~~~~~~~~~~~~

.. code-block:: python

   chuck = numchuck.ChucK()
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 44100)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)
   chuck.init()
   chuck.start()

   # Now safe to use

Check Compilation Results
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   success, shred_ids = chuck.compile_code(code)
   if not success:
       print("Compilation failed - check syntax")
       return

   # Use shred_ids safely
   for sid in shred_ids:
       info = chuck.get_shred_info(sid)

Clean Up Listeners
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register listener
   listener_id = chuck.listen_for_global_event("trigger", callback)

   # ... use it ...

   # Always clean up to prevent memory leaks
   chuck.stop_listening_for_global_event("trigger", listener_id)

Validate Buffers
~~~~~~~~~~~~~~~~

.. code-block:: python

   import numpy as np

   # Correct buffer types and sizes
   num_channels = chuck.get_param_int(numchuck.PARAM_OUTPUT_CHANNELS)
   input_buf = np.zeros(frames * 0, dtype=np.float32)  # Match input channels
   output_buf = np.zeros(frames * num_channels, dtype=np.float32)

   chuck.run(input_buf, output_buf, frames)

Error Recovery
--------------

Compilation Errors
~~~~~~~~~~~~~~~~~~

Continue after compilation failures:

.. code-block:: python

   # Try user code
   success, shred_ids = chuck.compile_code(user_code)
   if not success:
       print("Syntax error, trying fallback")
       # Try fallback
       success, shred_ids = chuck.compile_code(fallback_code)

VM Reset
~~~~~~~~

Clear VM state on errors:

.. code-block:: python

   try:
       # Complex operations
       pass
   except RuntimeError:
       # Reset VM state
       chuck.clear_vm()
       chuck.reset_shred_id()
       # Try again

Context Managers
~~~~~~~~~~~~~~~~

Use context managers for resource cleanup:

.. code-block:: python

   class ChuckContext:
       def __init__(self, sample_rate=44100, channels=2):
           self.chuck = numchuck.ChucK()
           self.sample_rate = sample_rate
           self.channels = channels

       def __enter__(self):
           self.chuck.set_param(numchuck.PARAM_SAMPLE_RATE, self.sample_rate)
           self.chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
           self.chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, self.channels)
           self.chuck.init()
           self.chuck.start()
           return self.chuck

       def __exit__(self, exc_type, exc_val, exc_tb):
           self.chuck.remove_all_shreds()
           return False

   # Usage
   with ChuckContext() as chuck:
       chuck.compile_code("SinOsc s => dac;")
       # Automatic cleanup on exit

Common Patterns
---------------

Safe Global Variable Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def safe_get_global_int(chuck, name, default=0):
       result = [default]

       def callback(value):
           result[0] = value

       try:
           chuck.get_global_int(name, callback)
           # Give time for callback
           time.sleep(0.1)
           return result[0]
       except RuntimeError:
           return default

Safe Event Listening
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class EventListener:
       def __init__(self, chuck, event_name):
           self.chuck = chuck
           self.event_name = event_name
           self.listener_id = None

       def start(self, callback):
           self.listener_id = self.chuck.listen_for_global_event(
               self.event_name, callback, listen_forever=True
           )

       def stop(self):
           if self.listener_id:
               self.chuck.stop_listening_for_global_event(
                   self.event_name, self.listener_id
               )
               self.listener_id = None

Debugging Tips
--------------

Check Initialization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   if not chuck.is_init():
       print("ChucK not initialized!")
       chuck.init()

Check VM Status
~~~~~~~~~~~~~~~

.. code-block:: python

   if not chuck.vm_running():
       print("VM not running!")
       chuck.start()

Monitor Shreds
~~~~~~~~~~~~~~

.. code-block:: python

   shreds = chuck.get_all_shred_ids()
   print(f"Active shreds: {len(shreds)}")

   for sid in shreds:
       info = chuck.get_shred_info(sid)
       print(f"  {info['id']}: {info['name']} - running={info['is_running']}")

Enable Verbose Output
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ChucK will print to stdout/stderr
   chuck.set_param(numchuck.PARAM_DUMP_INSTRUCTIONS, 1)

See Also
--------

* :doc:`api/chuck` - Complete ChucK class reference
* :doc:`quickstart` - Getting started guide
* :doc:`examples` - More code examples
