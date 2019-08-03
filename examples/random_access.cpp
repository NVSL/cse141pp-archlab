#include "archlab.h"
#include <stdlib.h>
#include <getopt.h>
#include "microbenchmarks.h"
#include <iostream>
#include<string.h>
#include<unistd.h>
#include <boost/program_options.hpp>
namespace po = boost::program_options;
#define SIZE_BASE ((4<<16)*KB)
#define SIZE_COUNT 1

int main(int argc, char *argv[]) {
  
  uint64_t mem_size_small;
  uint64_t mem_size_large;
  uint32_t read_ratio;
  uint64_t access_count;
  bool enable_demo;
  
  archlab_add_si_option<uint64_t>("mem-small",  mem_size_small, 4096 ,  "Small memory region size (bytes).");
  archlab_add_si_option<uint64_t>("mem-large",  mem_size_large, 32*MB,  "Large region size (bytes).");
  archlab_add_option<uint32_t>("read-ratio",     read_ratio    , 100  ,  "Read raio (percent).");
  archlab_add_si_option<uint64_t>("count",      access_count  , 1000 ,  "Accesses to perform.");
  archlab_add_flag("enable-demo", enable_demo, false ,  "Run demos.");
		     
  archlab_parse_cmd_line(&argc, argv);

    // Compute array size and allocate memory.
  int array_length = mem_size_large/sizeof(int);
  int * memory = (int *)calloc(array_length*sizeof(int), 1);

  if (memory == NULL) {
    fprintf(stderr, "Couldn't allocate memory.\n");
    exit(1);
  }

  // Using timer object
  for(auto mhz: cpu_frequencies) {
    for(uint64_t s = mem_size_small; s <= mem_size_large; s*= 2) {
      ArchLabTimer timer; // create it.
      pristine_machine(); // reset the machine
      set_cpu_clock_frequency(mhz);
      timer.
	attr("MemoryRange", s). // add key-value pairs.  strings, ints, and floats are fine for values.
	attr("ClockSpeed", mhz). 
	attr("Method", "function"). // Describing the measurement.
	go(); // Start measuring
      random_access(memory, s/sizeof(int), read_ratio, access_count);
      // Measurements tops when timer goes out of scope.
    }
  }
  
  if (enable_demo) {
    
    // Using C interface
    for(uint64_t s = mem_size_small; s <= mem_size_large; s*= 2) {
      pristine_machine(); // reset the machine 
      char size[1024];
      sprintf(size, "%lu", s);
      start_timing("MemoryRange",size, //You must provide at least 1 key-value pai describing the experiment in the C interface.
		   "Method", "C", // The keys and values all must be strings.
		   NULL); // End with NULL
      random_access(memory, s/sizeof(int), read_ratio, access_count); // Time this.
      stop_timing(); // Stop timing.
    }
    
    // Timer object + lambdas
    for(uint64_t s = mem_size_small; s <= mem_size_large; s*= 2) {
      ArchLabTimer timer;
      pristine_machine();
      timer.
	attr("MemoryRange", s).
	attr("Method", "lambda");
      
      timer.go([&]()->void{ // use a lambda.  you can put any code you
	  // want in the braces.  Not sure what the
	  // point of this, since you could write the
	  // code here as well.  Also the performance
	  // is potentially distorted.
	  uint64_t seed = 1;
	  register int s = 0;
	  for(register unsigned int i= 0; i < access_count; i++) {
	    register uint64_t t = fast_rand(&seed) % (array_length/sizeof(int));
	    if(fast_rand(&seed) % 100 > read_ratio) {
	      memory[t] = s;
	    } else {
	      s = memory[t];
	    }
	  }
	});
    }

  }
  
  archlab_write_stats();
  
  return 0;
}

