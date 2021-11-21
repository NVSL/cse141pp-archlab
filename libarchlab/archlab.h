#ifndef ARCHLAB_H_INCLUDED
#define ARCHLAB_H_INCLUDED
#include<stdint.h>
#include"walltime.h"
#include"fastrand.h"
//#define GETTIMEOFDAY

#ifdef GETTIMEOFDAY
#include <sys/time.h> // For struct timeval, gettimeofday
#else
#include <time.h> // For struct timespec, clock_gettime, CLOCK_MONOTONIC
#endif

#ifdef __cplusplus
#include<iostream>
#endif

#include <stdlib.h>

#define KB 1024
#define MB (1024*KB)
#define GB (1024*MB)

#define ARCHLAB_COLLECTOR_PAPI 1
#define ARCHLAB_COLLECTOR_PIN 2
#define ARCHLAB_COLLECTOR_NONE 3
#define ARCHLAB_COLLECTOR_ALLCORE 4

#ifdef __cplusplus
extern "C" {
#endif
  
	void archlab_init(int collector);

	void start_timing(const char * name,...);
	void stop_timing();
	void flush_caches();
	void pristine_machine();
	void set_cpu_clock_frequency(int mhz);  
	void write_csv(const char * filename);
	void load_frequencies();
	void track_stat(char *event);
	void clear_tracked_stats();

	uint64_t si_parse(const char *);
  
  
	void archlab_parse_cmd_line(int *argc, char *argv[]);
	void archlab_write_stats();

	extern int * cpu_frequencies_array;

	// These are fo signaling to pin tools to start and stop tracking
	// stats at a very fine grain.
	void archlab_start_quick() __attribute__((noinline));
	void archlab_start_quick();
	void archlab_stop_quick() __attribute__((noinline));
	void archlab_stop_quick();

	int archlab_canary(long int count);

#ifdef __cplusplus
} // C linkage
#endif

#include "archlab_impl.hpp"

#endif
