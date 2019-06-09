#include "archlab.h"
#include <stdlib.h>
#include <getopt.h>
#include "microbenchmarks.h"
#include "lab.h"
#include <stdio.h>
#include<string.h>
#include<unistd.h>


int go(int argc, char *argv[], void *args);

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

#define SIZE_BASE ((4<<16)*KB)
#define SIZE_COUNT 1

#if (0)
int main(int argc, char *argv[]) {

  archlab_parse_cmd_line(&argc, argv);

  struct sequential_read_args args;
  args.memory = (int *)malloc((SIZE_BASE << SIZE_COUNT)); // allocate a big vector

  if (args.memory == NULL) {
    fprintf(stderr, "Couldn't allocate memory.\n");
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
  
  archlab_write_stats();

  
  return 0;
}
#endif


#ifdef PAPI_TEST
int main(int argc, char *argv[]) {
  return 1;
}
#endif

#define PIN_TEST
#ifdef PIN_TEST
#include"pin-tools/dcache_archlab.hpp"

int main(int argc, char *argv[]) {
  return 1;
}
#endif


#if (0)
int main(int argc, char *argv[]) {
  
  archlab_parse_cmd_line(&argc, argv);

  
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
	  fprintf(stderr, "Incorrect result.\n");
	  exit(1);
	}
      }
      stop_timing(); // stop timing.
    }
  }

  archlab_write_stats();
  
  return 0;
}	

#endif
