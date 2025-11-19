ChucK Class
===========

.. currentmodule:: pychuck

.. autoclass:: ChucK
   :members:
   :undoc-members:
   :show-inheritance:

   .. rubric:: Initialization

   .. automethod:: __init__
   .. automethod:: init
   .. automethod:: start

   .. rubric:: Code Compilation

   .. automethod:: compile_code
   .. automethod:: compile_file

   .. rubric:: Audio Processing

   .. automethod:: run

   .. rubric:: Global Variables

   .. automethod:: set_global_int
   .. automethod:: set_global_float
   .. automethod:: set_global_string
   .. automethod:: get_global_int
   .. automethod:: get_global_float
   .. automethod:: get_global_string

   .. rubric:: Global Events

   .. automethod:: signal_global_event
   .. automethod:: broadcast_global_event
   .. automethod:: listen_for_global_event
   .. automethod:: stop_listening_for_global_event

   .. rubric:: Shred Management

   .. automethod:: remove_shred
   .. automethod:: remove_all_shreds
   .. automethod:: replace_shred
   .. automethod:: get_all_shred_ids
   .. automethod:: get_shred_info

   .. rubric:: VM Control

   .. automethod:: clear_vm
   .. automethod:: reset_shred_id

   .. rubric:: Status Methods

   .. automethod:: is_init
   .. automethod:: vm_running
   .. automethod:: now

   .. rubric:: Static Methods

   .. automethod:: version
   .. automethod:: int_size
   .. automethod:: num_vms
