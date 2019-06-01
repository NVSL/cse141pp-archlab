#ifndef ARCHLAB_INCLUDED
#define ARCHLAB_INCLUDED

#include<iostream>
#include <cpucounters.h>
#ifdef GETTIMEOFDAY
#include <sys/time.h> // For struct timeval, gettimeofday
#else
#include <time.h> // For struct timespec, clock_gettime, CLOCK_MONOTONIC
#endif

#include <stdlib.h>

#define KB 1024
#define MB (1024*KB)
#define GB (1024*MB)
  
struct Measurement {
  float time;
  SystemCounterState pcm_system_counter_state;
  std::vector<SocketCounterState> pcm_socket_counter_state;
  std::vector<CoreCounterState> pcm_core_counter_state;
};

struct MeasurementInterval {
  struct Measurement start;
  struct Measurement end;
};

void take_measurement(struct Measurement * measurement);

void archlab_init();
void write_system_config(const char * filename);
void write_system_config(std::ostream & out);
void write_run_stats(const char * filename,
		     struct Measurement * before,
		     struct Measurement * after) ; 
void write_run_stats(std::ostream & out,
		     struct Measurement * before,
		     struct Measurement * after);

int flush_caches();
int pristine_machine();
int set_cpu_clock_frequency(int mhz);

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

static inline int rand_int() {
  return rand();
}

static inline double rand_double() {
  return (rand() + 0.0)/(RAND_MAX + 0.0);
}
#endif
