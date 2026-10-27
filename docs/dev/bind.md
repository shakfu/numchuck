# Host classes via `ChucK::bind()`

User documentation: [api/host.md](../api/host.md). This page records design
decisions.

`ChucK::bind(queryFunc, name)` declares native classes in a VM's global
namespace, as a chugin's `ck_query` does. numchuck calls it in the `init`
binding, so every initialized instance has `Host`, `HostBuffer` and
`HostBufPlay`. The design follows chuck-max (`source/docs/dev/bind.md` there).
chuck-max and pd-chuck use the same class names, so a `.ck` file runs in all
three hosts.

## Files

- `src/hostbuffer.{h,cpp}`: `HostBuffer`, `HostBufPlay`. No Python
  dependency; another host can reuse them.
- `src/_numchuck.cpp`: `Host.msg`, `Host.send*`, the per-instance `HostState` registry,
  and the Python methods.

## `Host.msg` and `Host.send*` delivery

`Host.msg(name, ...)` goes to the one `on_msg` callback; `Host.send*` goes to
the `on_receive` callbacks for a name. The name `msg` is the outlet message
`msg <name> <args>` that chuck-max and pd-chuck emit, and mirrors their
`HostIn` receiving `msg`; `send*` keeps the `[send]`/`[receive]` idiom. It was
`Host.send(name, float)` until 2026-10-27; the bang, string and `float[]`
overloads came with the rename.

Synchronous: the callback runs inside the `Host.msg` call, on the VM thread.
chuck-max queues instead, because Max forbids outlet calls from the audio
thread. Python has no such rule, and numchuck's event and shred-watcher
callbacks already take the GIL on the VM thread. In offline `run()` the caller
already holds the GIL, so delivery is exact in logical time and costs no
thread switch.

`Host.sendBang`/`sendFloat`/`sendSymbol`/`sendList` follow the same rule.
With nothing queued, Pd's and Max's queue and message size give no reason
to cut lists, so lists arrive whole.

`sendList` takes `float[]` in all three hosts. ChucK arrays are homogeneous,
so a mixed list has no ChucK type; in Max and Pd the queue entry is also a
fixed array of 32 floats, so the audio thread allocates nothing. A `string[]`
overload is the next step if one host needs it.

- The callback always takes one argument: `None`, a `float`, a `str` or a
  `list[float]`. Passing a bang with no argument was rejected: a callback
  written for one call raised `TypeError` when the `.ck` file used another,
  and on the audio thread that only reaches `sys.unraisablehook`.
- An empty list arrives as `[]`, distinct from a bang's `None`. Pd turns it
  into a bang.
- The receiver registry is guarded by the GIL. Python mutates it, and
  delivery takes the GIL before reading it. An atomic receiver count lets a
  VM with no `on_receive` callbacks skip the GIL. A free-threaded build would
  need a mutex.
- Receivers are per instance, unlike Pd and Max, whose receive names are
  process-wide.

## `HostBuffer` here versus in chuck-max

chuck-max's `HostBuffer` must create `buffer~` references on the Max main
thread, so a name becomes ready a few ms after `name()`. Python registers
arrays itself, so numchuck drops that step, and the host interface
(`MaxBufferHost`) with it. One mutex per instance replaces `buffer_locksamples`.

`set_buffer` takes `nb::ndarray<float, c_contig>` with `noconvert()`. With
implicit conversion, a `float64` or strided array would be copied and ChucK's
`poke` would write to the copy.

## Lifetime

- A `HostState` is freed only when a new instance claims its `ChucK*`
  address, the same rule `release_instance_state` applies to taps. `shutdown()`
  cannot free it: the VM outlives that call, and `HostBuffer` objects cache the
  state pointer.
- `shutdown()` detaches the arrays and the callback instead, so Python objects
  are released on `close()`.
- An instance dropped without `close()` keeps its arrays until its address is
  reused.
- The registry map is heap-allocated and never destroyed. Static destruction
  runs after Python finalizes, and releasing an array then crashed the process
  (SIGSEGV at exit with a registered array).
