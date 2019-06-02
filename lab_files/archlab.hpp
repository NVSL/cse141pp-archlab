#ifndef ARCHLAB_INCLUDED
#define ARCHLAB_INCLUDED
#include<stdint.h>
#include<iostream>
#include <cpucounters.h>
#ifdef GETTIMEOFDAY
#include <sys/time.h> // For struct timeval, gettimeofday
#else
#include <time.h> // For struct timespec, clock_gettime, CLOCK_MONOTONIC
#endif
#include <json.hpp>
using json = nlohmann::json;

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
  json kv;
  struct Measurement start;
  struct Measurement end;
};
void archlab_init();

void measurement_interval_add_string(struct MeasurementInterval * m, char * name, char * value);
void measurement_interval_add_double(struct MeasurementInterval * m, char * name, double value);
void measurement_interval_start(struct MeasurementInterval * m, char * name);
void measurement_interval_stop(struct MeasurementInterval * m);

void start_timing(const char * name...);
void stop_timing();

void write_csv(const char * filename);
void write_csv(std::ostream & out);

void take_measurement(struct Measurement * measurement);


void measurement_interval_write_json(const char * filename,
				     struct MeasurementInterval * m);
void measurement_interval_write_json(std::ostream & out,
				     struct MeasurementInterval * m);
void measurement_interval_write_csv(const char * filename,
				    struct MeasurementInterval * m);
void measurement_interval_write_csv(std::ostream & out,
				    struct MeasurementInterval * m);

int flush_caches();
int pristine_machine();
int set_cpu_clock_frequency(int mhz);

static inline double wall_time ()
{
#ifdef GETTIMEOFDAY
#error
  struct timeval t;
  gettimeofday (&t, NULL);
  return 1.0*t.tv_sec + 1.e-6*t.tv_usec;
#else
  struct timespec t;
  clock_gettime (CLOCK_MONOTONIC, &t);
  return 1.0*t.tv_sec + 1.e-9*t.tv_nsec;
#endif
}

// default system random number generator
static inline uint64 rand_int() {
  return rand()*RAND_MAX + rand();
}

static inline double rand_double() {
  return (rand() + 0.0)/(RAND_MAX + 0.0);
}



#define TAP(a) (((a) == 0) ? 0 : ((1ull) << (((uint64_t)(a)) - (1ull))))

#define RAND_LFSR_DECL(BITS, T1, T2, T3, T4)				\
  inline static uint##BITS##_t RandLFSR##BITS(uint##BITS##_t *seed) {	\
    if (*seed == 0) {							\
      *seed = rand();							\
    }									\
    									\
    const uint##BITS##_t mask = TAP(T1) | TAP(T2) | TAP(T3) | TAP(T4);	\
    *seed = (*seed >> 1) ^ (uint##BITS##_t)(-(*seed & (uint##BITS##_t)(1)) & mask); \
    return *seed;							\
  }

RAND_LFSR_DECL(64, 64,63,61,60);
RAND_LFSR_DECL(32, 32,30,26,25);
RAND_LFSR_DECL(16, 16,14,13,11);
RAND_LFSR_DECL(8 ,  8, 6, 5, 4);

// Very fast (but not so random) random number generator.
inline static uint64_t RandLFSR(uint64_t * x) {
  return RandLFSR64(x);
}


#endif
