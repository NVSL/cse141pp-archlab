#include "lab_files/archlab.hpp"
#include <cstdlib>
#include <getopt.h>
#include "lab_files/microbenchmarks.hpp"
#include "lab.h"
#include<string.h>
#include<iostream>
#include<papi.h>

// from https://github.com/nlohmann/json
extern "C" {
  int go(int argc, char *argv[], void *args);
}

char * system_config_filename = strdup("system.json");
char * stats_filename = strdup("stats.json");

int data_collector_type = ARCHLAB_COLLECTOR_PAPI;

void parse_cmd_line(int argc, char *argv[]) {
  int c;

  while (1) {
    static struct option long_options[] =
      {
	{"stats-file",    required_argument,       0, 's'},
	{"no-counters",        no_argument,             0, 'n'},
	{"papi-counters",        no_argument,             0, 'p'},
	{"pcm-counters",        no_argument,             0, 'i'},
	{0, 0, 0, 0}
      };
    /* getopt_long stores the option index here. */
    int option_index = 0;
    
    c = getopt_long (argc, argv, "ns:",
		     long_options, &option_index);
    
    /* Detect the end of the options. */
    if (c == -1)
      break;
    
    switch (c)
      {
      case 's':
	stats_filename = strdup(optarg);
	break;
      case 'n':
	data_collector_type = ARCHLAB_COLLECTOR_NONE;
	break;
      case 'p':
	data_collector_type = ARCHLAB_COLLECTOR_PAPI;
	break;
      case 'i':
	data_collector_type = ARCHLAB_COLLECTOR_PCM;
	break;
      case '?':
	/* getopt_long already printed an error message. */
	break;

      default:
	abort ();
      }
  }
}

void naive(int argc, char * argv[], void* _args) {
  struct dot_product_args * args = (struct dot_product_args*)_args;
  double * A = args->A;
  double * B = args->B;
  int len = args->len;
  
  double sum = 0.0; 
  for(int i = 0; i < len; i++) {
    sum += A[i] * B[i];
  }

  args->sum =sum;
}

int cpu_frequencies[] = { // Table of frequencies our servers support.
  3500,
  3100,
  2900,
  2700,
  2500,
  2300,
  2100,
  2000,
  1800,
  1600,
  1400,
  1200,
  1000,
  800};
 
#define SIZE_BASE ((4<<16)*KB)
#define SIZE_COUNT 1

#if (0)
int main(int argc, char *argv[]) {

  parse_cmd_line(argc, argv);
  archlab_init(); // initialize lab infrastructure.
  struct sequential_read_args args;
  args.memory = (int *)malloc((SIZE_BASE << SIZE_COUNT)); // allocate a big vector

  if (args.memory == NULL) {
    std::cerr << "couldn't allocate memory." << std::endl;
    exit(1);
  }
  for(unsigned int i = 0; i < (SIZE_BASE <<  SIZE_COUNT)/sizeof(int); i++) {
    args.memory[i] = 0;
  }


  args.access_count = (8*MB)/sizeof(int) * 128; //Hit the whole L3 a couple times
  //  for(unsigned int j = 0; j < sizeof(cpu_frequencies)/sizeof(cpu_frequencies[0]); j++) { // Run the code at different frequencies
  for(int i = 0; i < SIZE_COUNT; i++) { // and for different vector sizes
    int size = SIZE_BASE << i; // compute vector size in bytes
    args.array_length= size/sizeof(int); // length in ints
    args.stride = 1;
    
    pristine_machine();
    set_cpu_clock_frequency(cpu_frequencies[0]); // set clock speed
    
    char name[1024];  // prepare two user-defined attributes for this run: vector size and clock speed
    sprintf(name, "%d", size);
    
    char clock[1024];
    sprintf(clock, "%dMHz", cpu_frequencies[0]);
    
    start_timing(name, // Start timing
		 "MemoryRangeSize", name, // pass NULL-terminated list of user-defined key-value pairs
		 "ClockSpeed", clock,
		 NULL);
    sequential_read(argc, argv, &args);  // Call submitted code
    stop_timing(); // stop timing.
  }
  //  }
  
  write_csv(stats_filename); // dump data for all runs.
  
  return 0;
}
#endif

#if (1)
int main(int argc, char *argv[]) {

  parse_cmd_line(argc, argv);
  archlab_init(data_collector_type); // initialize lab infrastructure.

  
  struct random_access_args args;
  args.memory = (int *)malloc((SIZE_BASE << SIZE_COUNT)); // allocate a big vector

  if (args.memory == NULL) {
    std::cerr << "couldn't allocate memory." << std::endl;
    exit(1);
  }
  for(unsigned int i = 0; i < (SIZE_BASE <<  SIZE_COUNT)/sizeof(int); i++) {
    args.memory[i] = 0;
  }
  papi_track_event(PAPI_TOT_INS);
  start_timing("test", // Start timing
	       NULL);
  for(int i =0; i <10000 ;i++) {}
  stop_timing(); // stop timing.
  write_csv(stats_filename); // dump data for all runs.
  return 0;
  
  args.read_ratio = 100;
  args.access_count = (8*MB)/sizeof(int) * 128; //Hit the whole L3 a couple times
  //  for(unsigned int j = 0; j < sizeof(cpu_frequencies)/sizeof(cpu_frequencies[0]); j++) { // Run the code at different frequencies
  for(int i = 0; i < SIZE_COUNT; i++) { // and for different vector sizes
    int size = SIZE_BASE << i; // compute vector size in bytes
    args.array_length= size/sizeof(int); // length in ints
    
    pristine_machine();
    set_cpu_clock_frequency(cpu_frequencies[0]); // set clock speed
    
    char name[1024];  // prepare two user-defined attributes for this run: vector size and clock speed
    sprintf(name, "%d", size);
    
    char clock[1024];
    sprintf(clock, "%dMHz", cpu_frequencies[0]);
    
    start_timing(name, // Start timing
		 "MemoryRangeSize", name, // pass NULL-terminated list of user-defined key-value pairs
		 "ClockSpeed", clock,
		 NULL);
    random_access(argc, argv, &args);  // Call submitted code
    stop_timing(); // stop timing.
  }
  //  }
  
  write_csv(stats_filename); // dump data for all runs.
  
  return 0;
}
#endif


  


#if (0)
int main(int argc, char *argv[]) {
  
  parse_cmd_line(argc, argv);
  archlab_init(); // initialize lab infrastructure. 
  
#define SIZE_COUNT 4
#define SIZE_BASE (4*MB)

#define ITERATIONS 20
    
  struct dot_product_args dp_args; // structure holds arguments and results, so we can provide inputs and check correctness.  Putting it in a struct means the interface is more invariant across labs.
  dp_args.A = (double *)malloc((SIZE_BASE << SIZE_COUNT)*sizeof(double)); // allocate two big vectors
  dp_args.B = (double *)malloc((SIZE_BASE << SIZE_COUNT)*sizeof(double));
  
  for(uint i = 0; i < (SIZE_BASE << SIZE_COUNT); i++) {
    dp_args.A[i] = rand_double(); // fill them with random data
    dp_args.B[i] = rand_double();
  }

  for(unsigned int j = 0; j < sizeof(cpu_frequencies)/sizeof(cpu_frequencies[0]); j++) { // Run the code at different frequencies
      
    for(int i = 0; i < SIZE_COUNT; i++) { // and for different vector sizes
      int size = SIZE_BASE << i; // compute vector size
      dp_args.len = size;

      naive(argc, argv, &dp_args); // compute correct answer
      double correct = dp_args.sum; // and record it
	
      pristine_machine(); // clear caches, disable turbo boost, reset clock speed
      set_cpu_clock_frequency(cpu_frequencies[j]); // set clock speed

      char name[1024];  // prepare two user-defined attributes for this run: vector size and clock speed
      sprintf(name, "%d", size);

      char clock[1024];
      sprintf(clock, "%dMHz", cpu_frequencies[j]);

      start_timing(name, // Start timing
		   "VectorSize", name, // pass NULL-terminated list of user-defined key-value pairs
		   "ClockSpeed", clock,
		   NULL);
      for(int k = 0; k < ITERATIONS; k++) {
	go(argc, argv, &dp_args);  // Call submitted code
	if (dp_args.sum != correct) {
	  std::cerr << "Incorrect result" << std::endl;
	  exit(1);
	}
      }
      stop_timing(); // stop timing.
    }
  }
  
  write_csv(stats_filename); // dump data for all runs.
  
  return 0;
}	

#endif
