// HostBuffer / HostBufPlay: ChucK reads and writes sample arrays the host
// registers by name. Adapted from chuck-max's HostBuffer (source/docs/dev/bind.md
// there). No Python dependency, so other hosts can reuse it.

#pragma once

#include "chuck_dl.h"

// distinct names per instance; a slot is never freed before its state
#define HOSTBUFFER_MAX_SLOTS 64

struct HostBufferState;

HostBufferState* hostbuffer_new();

// only once no VM can reach the state any more
void hostbuffer_free(HostBufferState* state);

// Any thread. Points 'name' at 'data' (interleaved, frames * chans floats).
// The caller keeps 'data' alive until it is replaced or cleared; once either
// call returns, the VM no longer touches the previous data. False if every
// slot is taken.
bool hostbuffer_set(HostBufferState* state, const char* name, float* data,
                    long frames, long chans, double sr);

// Any thread. False if 'name' had no data.
bool hostbuffer_clear(HostBufferState* state, const char* name);

void hostbuffer_clear_all(HostBufferState* state);

// maps a VM to its state; NULL if it has none
typedef HostBufferState* (*f_hostbuffer_lookup)(Chuck_VM* vm);

// set once, before any VM binds HostBuffer
void hostbuffer_set_lookup(f_hostbuffer_lookup lookup);

// ChucK::bind() query that declares HostBuffer and the HostBufPlay UGen
t_CKBOOL CK_DLL_CALL hostbuffer_query(Chuck_DL_Query* QUERY);
