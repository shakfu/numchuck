Audio Functions
===============

Real-time audio control functions for managing system audio.

Module Functions
----------------

.. autofunction:: numchuck.start_audio

.. autofunction:: numchuck.stop_audio

.. autofunction:: numchuck.shutdown_audio

.. autofunction:: numchuck.audio_info

Usage Examples
--------------

Start Audio
~~~~~~~~~~~

.. code-block:: python

   import numchuck

   # Start real-time audio with default device
   numchuck.start_audio()

   # Now audio will play through speakers
   chuck = numchuck.ChucK()
   chuck.init()
   chuck.compile_code("SinOsc s => dac; 440 => s.freq; 1::second => now;")

Stop Audio
~~~~~~~~~~

.. code-block:: python

   # Stop audio playback
   numchuck.stop_audio()

Shutdown Audio
~~~~~~~~~~~~~~

.. code-block:: python

   # Shutdown audio system with timeout
   numchuck.shutdown_audio(500)  # 500ms timeout

Query Audio Info
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get audio system information
   info = numchuck.audio_info()
   print(info)

Notes
-----

* Real-time audio requires audio hardware
* Use ``stop_audio()`` before ``shutdown_audio()``
* On some systems, audio may start automatically
* For offline rendering, audio system is not required

See Also
--------

* :doc:`chuck` - ChucK class for VM control
* :doc:`../examples` - More audio examples
