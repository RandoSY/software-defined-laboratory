#pragma once
// Host-only cooperative scheduler shim: each sleep advances fake millis().
// It does not reproduce Zephyr priorities, interrupts, or real thread timing.
#include "Arduino.h"
inline unsigned long k_uptime_get_32(){return millis();}
inline void k_msleep(int x){fakeTime()+=x;}

#define K_THREAD_STACK_DEFINE(n,s) static char n[s]
#define K_THREAD_STACK_SIZEOF(n) sizeof(n)
#define K_NO_WAIT 0
struct k_thread {};
inline int k_thread_create(k_thread*, char*, size_t, void (*entry)(void*,void*,void*), void*,void*,void*,int,int,int) { entry(nullptr,nullptr,nullptr); return 0; }
