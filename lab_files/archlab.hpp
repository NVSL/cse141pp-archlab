#ifndef LAB_INCLUDED
#define LAB_INCLUDED

#include<iostream>
#include <cpucounters.h>
#ifdef GETTIMEOFDAY
#include <sys/time.h> // For struct timeval, gettimeofday
#else
#include <time.h> // For struct timespec, clock_gettime, CLOCK_MONOTONIC
#endif


void archlab_init();
void write_system_config(const char * filename);
void write_system_config(std::ostream & out);
void write_run_stats(const char * filename,
		     const SystemCounterState & before,
		     const SystemCounterState & after);
void write_run_stats(std::ostream & out,
		     const SystemCounterState & before,
		     const SystemCounterState & after);

void flush_caches();
void pristine_machine();

static inline double wall_time ()
{
#ifdef GETTIMEOFDAY
  struct timeval t;
  gettimeofday (&t, NULL);
  return 1.*t.tv_sec + 1.e-6*t.tv_usec;
#else
  struct timespec t;
  clock_gettime (CLOCK_MONOTONIC, &t);
  return 1.*t.tv_sec + 1.e-9*t.tv_nsec;
#endif
}

#endif
