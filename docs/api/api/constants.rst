Constants
=========

Parameter and log level constants for ChucK configuration.

Parameter Constants
-------------------

These constants are used with ``ChucK.set_param()`` and ``ChucK.get_param()`` methods.

Audio Configuration
~~~~~~~~~~~~~~~~~~~

.. data:: numchuck.PARAM_SAMPLE_RATE

   Sample rate in Hz (e.g., 44100, 48000)

.. data:: numchuck.PARAM_INPUT_CHANNELS

   Number of input audio channels

.. data:: numchuck.PARAM_OUTPUT_CHANNELS

   Number of output audio channels

VM Configuration
~~~~~~~~~~~~~~~~

.. data:: numchuck.PARAM_VM_ADAPTIVE

   Enable adaptive VM execution

.. data:: numchuck.PARAM_VM_HALT

   Halt VM execution

.. data:: numchuck.PARAM_AUTO_DEPEND

   Enable automatic dependency resolution

.. data:: numchuck.PARAM_OTF_ENABLE

   Enable on-the-fly programming

.. data:: numchuck.PARAM_OTF_PORT

   Port for on-the-fly programming

Compilation
~~~~~~~~~~~

.. data:: numchuck.PARAM_DUMP_INSTRUCTIONS

   Dump VM instructions (debug)

.. data:: numchuck.PARAM_DEPRECATE_LEVEL

   Deprecation warning level

.. data:: numchuck.PARAM_CHUGIN_ENABLE

   Enable chugin (plugin) loading

.. data:: numchuck.PARAM_USER_CHUGINS

   User chugin search paths

File System
~~~~~~~~~~~

.. data:: numchuck.PARAM_WORKING_DIRECTORY

   Working directory for file operations

Version
~~~~~~~

.. data:: numchuck.PARAM_VERSION

   ChucK version string

Log Level Constants
-------------------

These constants control ChucK's logging verbosity.

.. data:: numchuck.LOG_NONE

   No logging

.. data:: numchuck.LOG_CORE

   Core system messages

.. data:: numchuck.LOG_SYSTEM

   System-level messages

.. data:: numchuck.LOG_HERALD

   Herald messages

.. data:: numchuck.LOG_WARNING

   Warning messages

.. data:: numchuck.LOG_INFO

   Informational messages

.. data:: numchuck.LOG_DEBUG

   Debug messages

.. data:: numchuck.LOG_FINE

   Fine-grained debug

.. data:: numchuck.LOG_FINER

   Finer-grained debug

.. data:: numchuck.LOG_FINEST

   Finest-grained debug

.. data:: numchuck.LOG_ALL

   All messages

Usage Examples
--------------

Set Parameters
~~~~~~~~~~~~~~

.. code-block:: python

   import numchuck

   chuck = numchuck.ChucK()

   # Audio configuration
   chuck.set_param(numchuck.PARAM_SAMPLE_RATE, 48000)
   chuck.set_param(numchuck.PARAM_INPUT_CHANNELS, 0)
   chuck.set_param(numchuck.PARAM_OUTPUT_CHANNELS, 2)

   # VM configuration
   chuck.set_param(numchuck.PARAM_VM_ADAPTIVE, 1)

   # Enable chugins
   chuck.set_param(numchuck.PARAM_CHUGIN_ENABLE, 1)

   chuck.init()

Get Parameters
~~~~~~~~~~~~~~

.. code-block:: python

   # Query current settings
   sample_rate = chuck.get_param_int(numchuck.PARAM_SAMPLE_RATE)
   channels = chuck.get_param_int(numchuck.PARAM_OUTPUT_CHANNELS)

   print(f"Sample rate: {sample_rate} Hz")
   print(f"Channels: {channels}")

Set Working Directory
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Set directory for ChucK file operations
   chuck.set_param_string(numchuck.PARAM_WORKING_DIRECTORY, "/path/to/files")

   # Now relative paths are resolved from this directory
   chuck.compile_file("melody.ck")

Enable Debug Output
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable instruction dumping for debugging
   chuck.set_param(numchuck.PARAM_DUMP_INSTRUCTIONS, 1)

   # ChucK will print VM instructions to stdout
   chuck.compile_code("SinOsc s => dac;")

Configure Logging
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Set log level (if supported by build)
   chuck.set_log_level(numchuck.LOG_INFO)

See Also
--------

* :doc:`chuck` - ChucK class reference
* :doc:`../quickstart` - Getting started guide
