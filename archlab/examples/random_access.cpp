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
  archlab_parse_cmd_line(&argc, argv);

  po::options_description desc("Measure performance with random accesses");
  desc.add_options()
    ("help", "print help")
    ("mem-small", po::value<si_uint64_t>()->default_value(4096), "Small memory region size (bytes).")
    ("mem-large", po::value<si_uint64_t>()->default_value(32*MB), "Large memory region size (bytes).")
    ("read-ratio",   po::value<int>()->default_value(100), "Read ratio (percent).")
    ("count", po::value<si_uint64_t>()->default_value(1000), "Accesses to perform.");
  
  po::parsed_options parsed = po::command_line_parser(argc, argv).options(desc).run();
  
  po::variables_map vm;
  po::store(parsed, vm);
  po::notify(vm);
  if (vm.count("help")) {
    std::cout << desc << std::endl;
    exit(0);
  }
  
  uint64_t mem_size_small = vm["mem-small"].as<si_uint64_t>();
  uint64_t mem_size_large = vm["mem-large"].as<si_uint64_t>();
  int read_ratio = vm["read-ratio"].as<int>();
  uint64_t access_count = vm["count"].as<si_uint64_t>();
    
  int array_length = mem_size_large/sizeof(int);
  int * memory = (int *)calloc(array_length*sizeof(int), 1);

  if (memory == NULL) {
    fprintf(stderr, "Couldn't allocate memory.\n");
    exit(1);
  }

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

  // Using timer object
  for(uint64_t s = mem_size_small; s <= mem_size_large; s*= 2) {
    ArchLabTimer timer; // create it.
    pristine_machine(); // reset the machine 
    timer("MemoryRange", s) // add key-value pairs.  strings, ints, and floats are fine for values.
      ("Method", "function") // Describing the measurement.
      .go(); // Start measuring
    random_access(memory, s/sizeof(int), read_ratio, access_count);
    // Measurements tops when timer goes out of scope.
  }

  // Timer object + lambdas
  for(uint64_t s = mem_size_small; s <= mem_size_large; s*= 2) {
    ArchLabTimer timer;
    pristine_machine();
    timer("MemoryRange", s) // Same as above 
      ("Method", "lambda")
      .go([&]()->void{ // use a lambda.   you can put any code you want in the braces.
	random_access(memory, s/sizeof(int), read_ratio, access_count);
      });
  }

  archlab_write_stats();
  
  return 0;
}

