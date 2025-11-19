#!/usr/bin/env python3
"""
Simple performance benchmarks for pychuck.

Measures basic operations to establish performance baselines.
"""

import time
import numpy as np
import pychuck


def benchmark(name, func, iterations=100):
    """Run a benchmark and print results."""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()

    total_time = end - start
    avg_time = total_time / iterations
    ops_per_sec = iterations / total_time if total_time > 0 else 0

    print(f"{name}:")
    print(f"  Iterations:  {iterations}")
    print(f"  Total time:  {total_time:.4f}s")
    print(f"  Avg time:    {avg_time * 1000:.4f}ms")
    print(f"  Ops/sec:     {ops_per_sec:.2f}")
    print()


def main():
    print("=" * 60)
    print("pychuck Simple Performance Benchmarks")
    print("=" * 60)
    print()

    #
    # 1. Compilation benchmark
    #
    print("1. Code Compilation")
    print("-" * 60)

    chuck = pychuck.ChucK()
    chuck.set_param(pychuck.PARAM_SAMPLE_RATE, 44100)
    chuck.set_param(pychuck.PARAM_INPUT_CHANNELS, 0)
    chuck.set_param(pychuck.PARAM_OUTPUT_CHANNELS, 2)
    chuck.init()

    code = "SinOsc s => dac; 440 => s.freq;"

    def compile_and_remove():
        success, shred_ids = chuck.compile_code(code)
        if success and shred_ids:
            chuck.remove_shred(shred_ids[0])

    benchmark("Simple code compilation", compile_and_remove, 100)

    #
    # 2. Audio rendering benchmark
    #
    print("2. Audio Rendering")
    print("-" * 60)

    # Compile once for rendering tests
    code_with_time = """
        SinOsc s => dac;
        440 => s.freq;
        0.5 => s.gain;
        while(true) { 1::samp => now; }
    """
    chuck.compile_code(code_with_time)

    frames = 512
    input_buf = np.zeros(frames * 0, dtype=np.float32)
    output_buf = np.zeros(frames * 2, dtype=np.float32)

    def render_audio():
        chuck.run(input_buf, output_buf, frames)

    benchmark("Audio rendering (512 frames)", render_audio, 200)

    # Calculate throughput
    samples_per_call = frames * 2
    bytes_per_call = samples_per_call * 4  # float32
    iterations = 200
    start = time.perf_counter()
    for _ in range(iterations):
        render_audio()
    elapsed = time.perf_counter() - start
    throughput_mb_s = (bytes_per_call * iterations) / elapsed / (1024 * 1024)
    print(f"  Throughput:  {throughput_mb_s:.2f} MB/s")
    print()

    chuck.clear_vm()

    #
    # 3. Global variable access
    #
    print("3. Global Variable Access")
    print("-" * 60)

    chuck.compile_code("global int counter;")

    def set_global():
        chuck.set_global_int("counter", 42)

    benchmark("Set global int", set_global, 500)

    chuck.clear_vm()

    #
    # 4. Event signaling
    #
    print("4. Event Signaling")
    print("-" * 60)

    chuck.compile_code("global Event trigger;")

    def signal_event():
        chuck.signal_global_event("trigger")

    benchmark("Signal event", signal_event, 500)

    chuck.clear_vm()

    print("=" * 60)
    print("Benchmark Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
