# Host classes

Every VM has three classes the host program binds at `init()`:

| Class | Direction | Purpose |
|-|-|-|
| `Host` | ChucK to Python | `Host.msg(name, ...)` calls the `on_msg` callback; `Host.sendBang`/`sendFloat`/`sendSymbol`/`sendList` call the `on_receive` callbacks for a name |
| `HostBuffer` | both | read and write a numpy array by name |
| `HostBufPlay` | Python to ChucK | UGen that plays one channel of a numpy array |

chuck-max and pd-chuck bind the same names, so a `.ck` file that uses only
the members listed here runs in each. Both add host-specific classes
(`HostIn`, and `HostClock` in chuck-max).

## `Host.msg`

```python
chuck.on_msg(lambda name, value: print(name, value))
chuck.compile("""
    while (true) {
        Math.random2f(200, 800) => float f;
        Host.msg("freq", f);
        250::ms => now;
    }
""")
chuck.run(chuck.sample_rate)   # one second: prints 4 lines
```

`Host.msg` calls the `on_msg` callback; `Host.send*` calls the `on_receive`
callbacks for a name. In Max and Pd, `Host.msg` emits `msg <name> <args>`
from the `chuck~` reply outlet, the message `HostIn` receives in the other
direction.

Without `Host.msg`, sending a value to Python takes a `global float`, a
`global Event`, an `on_event` listener and a `get_float` call.

| ChucK call | Callback arguments |
|-|-|
| `msg(name)` | `name, None` |
| `msg(name, value)` | `name, float` |
| `msg(name, string)` | `name, str` |
| `msg(name, values)` | `name, list[float]`, whole; an empty list is `[]` |

In Max and Pd an empty list sends `msg <name>`, the bang form.

- The callback runs during `run()`, at the shred's logical time:
  `chuck.raw.now()` inside it returns the time of the `Host.msg` call.
- During real-time audio it runs on the audio thread and takes the GIL.
  Keep it short, or put the value on a `queue.Queue`.
- An exception in the callback goes to `sys.unraisablehook`, as for every
  VM callback ([events](events.md)).
- One callback per instance. `on_msg(None)` clears it.

## `Host.sendBang` / `sendFloat` / `sendSymbol` / `sendList`

```python
chuck.on_receive("tick", lambda _: print("tick"))
chuck.on_receive("freq", lambda f: print("freq", f))
chuck.on_receive("range", lambda s: print("range", s))
chuck.on_receive("pair", lambda values: print("pair", values))
chuck.compile("""
    Host.sendBang("tick");
    Host.sendFloat("freq", 440);
    Host.sendSymbol("range", "low");
    Host.sendList("pair", [440.0, 0.2]);
""")
chuck.run(1)
```

In Pd and Max these calls reach every `[receive <name>]`. `on_receive`
registers the Python counterpart of a `[receive]`. The callback always takes
one argument, whichever call ChucK makes. A `[receive]` accepts any message,
so a callback must too; one that expected no argument would raise as soon
as the `.ck` file sent the name a float.

| ChucK call | Callback argument |
|-|-|
| `sendBang(name)` | `None` |
| `sendFloat(name, value)` | `float` |
| `sendSymbol(name, symbol)` | `str` |
| `sendList(name, values)` | `list[float]`, whole; an empty list is `[]` |

- Several callbacks can share a name. They run in registration order.
- A name with no callback is skipped, as `[send]` skips a missing `[receive]`.
- Receivers belong to one `Chuck` instance. Pd and Max receive names are
  shared by the whole process, so two `chuck~` objects reach the same
  `[r freq]`. Here, a shred in one instance does not reach another instance's
  callbacks. To hear both, register the callback on each.
- `on_receive` returns an id. `remove_receiver(name, id)` removes the callback.
  A callback may remove itself.
- Delivery is as for `Host.msg`: during `run()`, at the shred's logical time,
  on the VM thread. Exceptions go to `sys.unraisablehook`.
- Unlike Pd and Max, nothing is queued, so there is no 256-call limit. Lists
  are not cut to 32 elements, and an empty list is not turned into a bang.
- Lists hold floats only, in every host. ChucK arrays are homogeneous, so a
  mixed list such as `["note", 60]` has no ChucK type. Send a string with
  `sendSymbol`.

## `HostBuffer`

```python
buf = np.zeros((48000, 2), dtype=np.float32)
chuck.set_buffer("rec", buf)
chuck.compile("""
    HostBuffer b;
    b.name("rec");
    for (0 => int i; i < b.frames(); i++) {
        b.poke(i, 0, Math.sin(2 * pi * 440 * i / b.sampleRate()));
    }
""")
chuck.run(1)
# buf[:, 0] now holds a 440 Hz sine
```

ChucK reads and writes the array in place, without copying it.
`set_buffer` accepts only a writable, C-contiguous `float32` array of shape
`(frames,)` or `(frames, channels)`. Anything else raises rather than being
copied, because ChucK's writes would go to the copy.

| Method | Returns |
|-|-|
| `name(string)`, `name()` | the name, or `""` when 64 names are in use |
| `ready()` | 1 once Python has registered an array under the name |
| `frames()`, `channels()`, `sampleRate()` | 0 if not ready |
| `peek(frame)`, `peek(frame, chan)` | 0 if out of range or not ready |
| `poke(frame, value)`, `poke(frame, chan, value)` | ignored if out of range |

Channels count from 0. `sampleRate()` is the `sample_rate` passed to
`set_buffer`, defaulting to the VM's.

`set_buffer` on a registered name replaces the array. `remove_buffer`
detaches it, and ChucK then reads 0. A ChucK object that named the buffer
before Python registered it sees the array as soon as it is registered.

## `HostBufPlay`

```python
chuck.set_buffer("loop", samples)
chuck.compile("""
    HostBufPlay p => dac;
    p.name("loop");       // restarts from frame 0
    1 => p.loop;
    -0.5 => p.rate;       // half speed, backward
    1::day => now;
""")
```

- `name`, `ready()`, `frames()`: as `HostBuffer`.
- `pos` (frames), `rate`, `loop` (default 0), `interp` (1 linear, the
  default; 0 none), `channel` (from 0).
- Without `loop`, playback stops at either end and outputs 0.
- An array registered at another `sample_rate` plays at its own pitch.
- Silent while no array is registered. The position holds, so playback
  resumes when one is.

## Limits

- 64 buffer names per instance. A name stays claimed until the instance is
  destroyed, including across `clear()`.
- Each `peek`, `poke` and `HostBufPlay` sample takes a mutex. Python takes it
  only for the length of a pointer swap in `set_buffer` and `remove_buffer`.
- Python writes to a registered array while real-time audio runs are not
  synchronized with ChucK's reads. A sample can be read mid-update. Swap
  arrays with `set_buffer` instead.

Design notes: [bind.md](../dev/bind.md).
