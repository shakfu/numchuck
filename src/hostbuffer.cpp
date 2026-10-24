#include "hostbuffer.h"

#include "chuck_oo.h"
#include "chuck_vm.h"

#include <cmath>
#include <mutex>
#include <string>

struct HostBufferSlot {
    std::string name;
    float* data = nullptr;  // NULL while the host has registered nothing
    long frames = 0;
    long chans = 0;
    double sr = 0;
};

// One mutex guards every slot. The VM thread holds it for a single sample
// access; the host holds it only to swap a slot's pointer.
struct HostBufferState {
    std::mutex lock;
    HostBufferSlot slots[HOSTBUFFER_MAX_SLOTS];
    int count = 0;
};

static f_hostbuffer_lookup g_lookup = NULL;

// member offsets, the same for every VM that binds the class
static t_CKUINT hostbuffer_offset_state = 0;
static t_CKUINT hostbuffer_offset_slot = 0;

HostBufferState* hostbuffer_new()
{
    return new HostBufferState;
}

void hostbuffer_free(HostBufferState* state)
{
    delete state;
}

void hostbuffer_set_lookup(f_hostbuffer_lookup lookup)
{
    g_lookup = lookup;
}

// caller holds state->lock; -1 when all slots are taken
static int slot_for(HostBufferState* state, const std::string& name)
{
    for (int i = 0; i < state->count; i++) {
        if (state->slots[i].name == name) {
            return i;
        }
    }
    if (state->count == HOSTBUFFER_MAX_SLOTS) {
        return -1;
    }
    state->slots[state->count].name = name;
    return state->count++;
}

bool hostbuffer_set(HostBufferState* state, const char* name, float* data,
                    long frames, long chans, double sr)
{
    std::lock_guard<std::mutex> guard(state->lock);
    int i = slot_for(state, name);
    if (i < 0) {
        return false;
    }
    HostBufferSlot& s = state->slots[i];
    s.data = data;
    s.frames = frames;
    s.chans = chans;
    s.sr = sr;
    return true;
}

bool hostbuffer_clear(HostBufferState* state, const char* name)
{
    std::lock_guard<std::mutex> guard(state->lock);
    for (int i = 0; i < state->count; i++) {
        HostBufferSlot& s = state->slots[i];
        if (s.name == name) {
            bool had = s.data != nullptr;
            s.data = nullptr;
            s.frames = s.chans = 0;
            s.sr = 0;
            return had;
        }
    }
    return false;
}

void hostbuffer_clear_all(HostBufferState* state)
{
    std::lock_guard<std::mutex> guard(state->lock);
    for (int i = 0; i < state->count; i++) {
        state->slots[i].data = nullptr;
        state->slots[i].frames = state->slots[i].chans = 0;
        state->slots[i].sr = 0;
    }
}

static int claim_slot(HostBufferState* state, Chuck_String* name)
{
    if (state == NULL || name == NULL) {
        return -1;
    }
    std::lock_guard<std::mutex> guard(state->lock);
    return slot_for(state, name->str());
}

static std::string slot_name(HostBufferState* state, t_CKINT slot)
{
    if (state == NULL || slot < 0) {
        return "";
    }
    std::lock_guard<std::mutex> guard(state->lock);
    return state->slots[slot].name;
}


//-----------------------------------------------------------------------------
// a slot held locked for one access

class Locked {
public:
    Locked(HostBufferState* state, t_CKINT slot) : m_state(state)
    {
        if (state == NULL || slot < 0) {
            return;
        }
        state->lock.lock();
        m_slot = &state->slots[slot];
        if (m_slot->data == nullptr) {
            m_slot = nullptr;
            state->lock.unlock();
        }
    }
    ~Locked()
    {
        if (m_slot) {
            m_state->lock.unlock();
        }
    }
    Locked(const Locked&) = delete;
    Locked& operator=(const Locked&) = delete;

    // NULL if the host has registered nothing under the name
    const HostBufferSlot* operator->() const { return m_slot; }
    explicit operator bool() const { return m_slot != nullptr; }

    bool in_range(t_CKINT frame, t_CKINT chan) const
    {
        return frame >= 0 && frame < m_slot->frames && chan >= 0 && chan < m_slot->chans;
    }
    float& at(long frame, t_CKINT chan) const
    {
        return m_slot->data[frame * m_slot->chans + chan];
    }

private:
    HostBufferState* m_state;
    const HostBufferSlot* m_slot = nullptr;
};


//-----------------------------------------------------------------------------
// HostBuffer

static HostBufferState* state_of(Chuck_Object* self)
{
    return (HostBufferState*)OBJ_MEMBER_INT(self, hostbuffer_offset_state);
}

static t_CKINT slot_of(Chuck_Object* self)
{
    return OBJ_MEMBER_INT(self, hostbuffer_offset_slot);
}

CK_DLL_CTOR(hostbuffer_ctor)
{
    // the host frees the state after the VM, so caching it here is safe
    OBJ_MEMBER_INT(SELF, hostbuffer_offset_state) = (t_CKINT)(g_lookup ? g_lookup(VM) : NULL);
    OBJ_MEMBER_INT(SELF, hostbuffer_offset_slot) = -1;
}

CK_DLL_MFUN(hostbuffer_set_name)
{
    HostBufferState* st = state_of(SELF);
    t_CKINT slot = claim_slot(st, GET_NEXT_STRING(ARGS));
    OBJ_MEMBER_INT(SELF, hostbuffer_offset_slot) = slot;
    RETURN->v_string = (Chuck_String*)API->object->create_string(
        VM, slot_name(st, slot).c_str(), FALSE);
}

CK_DLL_MFUN(hostbuffer_get_name)
{
    RETURN->v_string = (Chuck_String*)API->object->create_string(
        VM, slot_name(state_of(SELF), slot_of(SELF)).c_str(), FALSE);
}

CK_DLL_MFUN(hostbuffer_ready)
{
    RETURN->v_int = (bool)Locked(state_of(SELF), slot_of(SELF));
}

CK_DLL_MFUN(hostbuffer_frames)
{
    Locked b(state_of(SELF), slot_of(SELF));
    RETURN->v_int = b ? b->frames : 0;
}

CK_DLL_MFUN(hostbuffer_channels)
{
    Locked b(state_of(SELF), slot_of(SELF));
    RETURN->v_int = b ? b->chans : 0;
}

CK_DLL_MFUN(hostbuffer_sample_rate)
{
    Locked b(state_of(SELF), slot_of(SELF));
    RETURN->v_float = b ? b->sr : 0;
}

static t_CKFLOAT peek(Chuck_Object* self, t_CKINT frame, t_CKINT chan)
{
    Locked b(state_of(self), slot_of(self));
    return (b && b.in_range(frame, chan)) ? b.at(frame, chan) : 0;
}

static void poke(Chuck_Object* self, t_CKINT frame, t_CKINT chan, t_CKFLOAT value)
{
    Locked b(state_of(self), slot_of(self));
    if (b && b.in_range(frame, chan)) {
        b.at(frame, chan) = (float)value;
    }
}

CK_DLL_MFUN(hostbuffer_peek)
{
    t_CKINT frame = GET_NEXT_INT(ARGS);
    RETURN->v_float = peek(SELF, frame, 0);
}

CK_DLL_MFUN(hostbuffer_peek_chan)
{
    t_CKINT frame = GET_NEXT_INT(ARGS);
    t_CKINT chan = GET_NEXT_INT(ARGS);
    RETURN->v_float = peek(SELF, frame, chan);
}

CK_DLL_MFUN(hostbuffer_poke)
{
    t_CKINT frame = GET_NEXT_INT(ARGS);
    t_CKFLOAT value = GET_NEXT_FLOAT(ARGS);
    poke(SELF, frame, 0, value);
    RETURN->v_float = value;
}

CK_DLL_MFUN(hostbuffer_poke_chan)
{
    t_CKINT frame = GET_NEXT_INT(ARGS);
    t_CKINT chan = GET_NEXT_INT(ARGS);
    t_CKFLOAT value = GET_NEXT_FLOAT(ARGS);
    poke(SELF, frame, chan, value);
    RETURN->v_float = value;
}


//-----------------------------------------------------------------------------
// HostBufPlay: plays one channel of a host buffer as a UGen

static t_CKUINT hostbufplay_offset_data = 0;

struct BufPlay {
    HostBufferState* state;
    t_CKINT slot;
    double pos;      // in frames
    double rate;
    double vm_sr;
    t_CKINT loop;
    t_CKINT interp;  // 0 none, 1 linear
    t_CKINT chan;
};

static BufPlay* bufplay_of(Chuck_Object* self)
{
    return (BufPlay*)OBJ_MEMBER_INT(self, hostbufplay_offset_data);
}

CK_DLL_CTOR(hostbufplay_ctor)
{
    BufPlay* p = new BufPlay;
    p->state = g_lookup ? g_lookup(VM) : NULL;
    p->slot = -1;
    p->pos = 0;
    p->rate = 1;
    p->vm_sr = (double)API->vm->srate(VM);
    p->loop = 0;
    p->interp = 1;
    p->chan = 0;
    OBJ_MEMBER_INT(SELF, hostbufplay_offset_data) = (t_CKINT)p;
}

CK_DLL_DTOR(hostbufplay_dtor)
{
    delete bufplay_of(SELF);
    OBJ_MEMBER_INT(SELF, hostbufplay_offset_data) = 0;
}

// one lock per sample, as in HostBuffer.peek, but without a shred step
CK_DLL_TICK(hostbufplay_tick)
{
    BufPlay* p = bufplay_of(SELF);
    *out = 0;
    Locked b(p->state, p->slot);
    if (!b) {
        return TRUE;
    }
    double n = (double)b->frames;
    if (n > 0 && p->chan >= 0 && p->chan < b->chans) {
        if (p->loop) {
            p->pos = std::fmod(p->pos, n);
            if (p->pos < 0) {
                p->pos += n;
            }
        }
        if (p->pos >= 0 && p->pos < n) {
            long i = (long)p->pos;
            double x = b.at(i, p->chan);
            if (p->interp) {
                // past the last frame: wrap when looping, else hold
                long j = (i + 1 < b->frames) ? i + 1 : (p->loop ? 0 : i);
                x += (p->pos - i) * (b.at(j, p->chan) - x);
            }
            *out = (SAMPLE)x;
            // a buffer at another rate plays at its own pitch, as SndBuf does
            p->pos += p->rate * (b->sr > 0 ? b->sr / p->vm_sr : 1);
        }
    }
    return TRUE;
}

CK_DLL_MFUN(hostbufplay_set_name)
{
    BufPlay* p = bufplay_of(SELF);
    p->slot = claim_slot(p->state, GET_NEXT_STRING(ARGS));
    p->pos = 0;
    RETURN->v_string = (Chuck_String*)API->object->create_string(
        VM, slot_name(p->state, p->slot).c_str(), FALSE);
}

CK_DLL_MFUN(hostbufplay_get_name)
{
    BufPlay* p = bufplay_of(SELF);
    RETURN->v_string = (Chuck_String*)API->object->create_string(
        VM, slot_name(p->state, p->slot).c_str(), FALSE);
}

CK_DLL_MFUN(hostbufplay_ready)
{
    BufPlay* p = bufplay_of(SELF);
    RETURN->v_int = (bool)Locked(p->state, p->slot);
}

CK_DLL_MFUN(hostbufplay_frames)
{
    BufPlay* p = bufplay_of(SELF);
    Locked b(p->state, p->slot);
    RETURN->v_int = b ? b->frames : 0;
}

CK_DLL_MFUN(hostbufplay_set_pos)
{
    bufplay_of(SELF)->pos = (double)GET_NEXT_INT(ARGS);
    RETURN->v_int = (t_CKINT)bufplay_of(SELF)->pos;
}

CK_DLL_MFUN(hostbufplay_get_pos)
{
    RETURN->v_int = (t_CKINT)std::floor(bufplay_of(SELF)->pos);
}

CK_DLL_MFUN(hostbufplay_set_rate)
{
    RETURN->v_float = bufplay_of(SELF)->rate = GET_NEXT_FLOAT(ARGS);
}

CK_DLL_MFUN(hostbufplay_get_rate)
{
    RETURN->v_float = bufplay_of(SELF)->rate;
}

CK_DLL_MFUN(hostbufplay_set_loop)
{
    RETURN->v_int = bufplay_of(SELF)->loop = GET_NEXT_INT(ARGS) != 0;
}

CK_DLL_MFUN(hostbufplay_get_loop)
{
    RETURN->v_int = bufplay_of(SELF)->loop;
}

CK_DLL_MFUN(hostbufplay_set_interp)
{
    RETURN->v_int = bufplay_of(SELF)->interp = GET_NEXT_INT(ARGS) != 0;
}

CK_DLL_MFUN(hostbufplay_get_interp)
{
    RETURN->v_int = bufplay_of(SELF)->interp;
}

CK_DLL_MFUN(hostbufplay_set_channel)
{
    RETURN->v_int = bufplay_of(SELF)->chan = GET_NEXT_INT(ARGS);
}

CK_DLL_MFUN(hostbufplay_get_channel)
{
    RETURN->v_int = bufplay_of(SELF)->chan;
}

static void query_hostbufplay(Chuck_DL_Query* QUERY)
{
    QUERY->begin_class(QUERY, "HostBufPlay", "UGen");
    QUERY->doc_class(QUERY, "plays one channel of a named host buffer; "
                            "silent while the host has registered none");
    QUERY->add_ctor(QUERY, hostbufplay_ctor);
    QUERY->add_dtor(QUERY, hostbufplay_dtor);
    QUERY->add_ugen_func(QUERY, hostbufplay_tick, NULL, 1, 1);
    hostbufplay_offset_data = QUERY->add_mvar(QUERY, "int", "@data", FALSE);

    QUERY->add_mfun(QUERY, hostbufplay_set_name, "string", "name");
    QUERY->add_arg(QUERY, "string", "name");
    QUERY->doc_func(QUERY, "play the buffer with this name, from frame 0");
    QUERY->add_mfun(QUERY, hostbufplay_get_name, "string", "name");
    QUERY->doc_func(QUERY, "the buffer name, or \"\"");
    QUERY->add_mfun(QUERY, hostbufplay_ready, "int", "ready");
    QUERY->doc_func(QUERY, "1 if the host has registered the buffer");
    QUERY->add_mfun(QUERY, hostbufplay_frames, "int", "frames");
    QUERY->doc_func(QUERY, "length in sample frames; 0 if not ready");
    QUERY->add_mfun(QUERY, hostbufplay_set_pos, "int", "pos");
    QUERY->add_arg(QUERY, "int", "frame");
    QUERY->doc_func(QUERY, "set the play position in frames");
    QUERY->add_mfun(QUERY, hostbufplay_get_pos, "int", "pos");
    QUERY->doc_func(QUERY, "the play position in frames");
    QUERY->add_mfun(QUERY, hostbufplay_set_rate, "float", "rate");
    QUERY->add_arg(QUERY, "float", "rate");
    QUERY->doc_func(QUERY, "playback rate; 1 is normal, negative plays backward");
    QUERY->add_mfun(QUERY, hostbufplay_get_rate, "float", "rate");
    QUERY->doc_func(QUERY, "playback rate");
    QUERY->add_mfun(QUERY, hostbufplay_set_loop, "int", "loop");
    QUERY->add_arg(QUERY, "int", "loop");
    QUERY->doc_func(QUERY, "1 loops; 0 (default) stops at either end");
    QUERY->add_mfun(QUERY, hostbufplay_get_loop, "int", "loop");
    QUERY->doc_func(QUERY, "1 if looping");
    QUERY->add_mfun(QUERY, hostbufplay_set_interp, "int", "interp");
    QUERY->add_arg(QUERY, "int", "interp");
    QUERY->doc_func(QUERY, "1 (default) linear interpolation; 0 none");
    QUERY->add_mfun(QUERY, hostbufplay_get_interp, "int", "interp");
    QUERY->doc_func(QUERY, "1 if interpolating");
    QUERY->add_mfun(QUERY, hostbufplay_set_channel, "int", "channel");
    QUERY->add_arg(QUERY, "int", "chan");
    QUERY->doc_func(QUERY, "buffer channel to play, from 0");
    QUERY->add_mfun(QUERY, hostbufplay_get_channel, "int", "channel");
    QUERY->doc_func(QUERY, "buffer channel being played");
    QUERY->end_class(QUERY);
}

t_CKBOOL CK_DLL_CALL hostbuffer_query(Chuck_DL_Query* QUERY)
{
    QUERY->begin_class(QUERY, "HostBuffer", "Object");
    QUERY->doc_class(QUERY, "reads and writes the samples of a buffer the host "
                            "registers by name");
    QUERY->add_ctor(QUERY, hostbuffer_ctor);
    hostbuffer_offset_state = QUERY->add_mvar(QUERY, "int", "@state", FALSE);
    hostbuffer_offset_slot = QUERY->add_mvar(QUERY, "int", "@slot", FALSE);

    QUERY->add_mfun(QUERY, hostbuffer_set_name, "string", "name");
    QUERY->add_arg(QUERY, "string", "name");
    QUERY->doc_func(QUERY, "refer to the buffer with this name; returns the "
                           "name, or \"\" if 64 names are already in use");
    QUERY->add_mfun(QUERY, hostbuffer_get_name, "string", "name");
    QUERY->doc_func(QUERY, "the buffer name, or \"\"");
    QUERY->add_mfun(QUERY, hostbuffer_ready, "int", "ready");
    QUERY->doc_func(QUERY, "1 if the host has registered the buffer");
    QUERY->add_mfun(QUERY, hostbuffer_frames, "int", "frames");
    QUERY->doc_func(QUERY, "length in sample frames; 0 if not ready");
    QUERY->add_mfun(QUERY, hostbuffer_channels, "int", "channels");
    QUERY->doc_func(QUERY, "number of channels; 0 if not ready");
    QUERY->add_mfun(QUERY, hostbuffer_sample_rate, "float", "sampleRate");
    QUERY->doc_func(QUERY, "the buffer sample rate; 0 if not ready");

    QUERY->add_mfun(QUERY, hostbuffer_peek, "float", "peek");
    QUERY->add_arg(QUERY, "int", "frame");
    QUERY->doc_func(QUERY, "sample at frame, channel 0; 0 if out of range");
    QUERY->add_mfun(QUERY, hostbuffer_peek_chan, "float", "peek");
    QUERY->add_arg(QUERY, "int", "frame");
    QUERY->add_arg(QUERY, "int", "chan");
    QUERY->doc_func(QUERY, "sample at frame and channel (from 0); 0 if out of range");
    QUERY->add_mfun(QUERY, hostbuffer_poke, "float", "poke");
    QUERY->add_arg(QUERY, "int", "frame");
    QUERY->add_arg(QUERY, "float", "value");
    QUERY->doc_func(QUERY, "write value at frame, channel 0; ignored if out of range");
    QUERY->add_mfun(QUERY, hostbuffer_poke_chan, "float", "poke");
    QUERY->add_arg(QUERY, "int", "frame");
    QUERY->add_arg(QUERY, "int", "chan");
    QUERY->add_arg(QUERY, "float", "value");
    QUERY->doc_func(QUERY, "write value at frame and channel (from 0); ignored if out of range");
    QUERY->end_class(QUERY);

    query_hostbufplay(QUERY);
    return TRUE;
}
