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
    ("memory-size-small",po::value<size_t>()->default_value(4096), "Small memory region size (bytes).")
    ("memory-size-large",po::value<size_t>()->default_value(32*MB), "Large memory region size (bytes).")
    ("read-ratio",   po::value<int>()->default_value(100), "Read ratio (percent).")
    ("access-count", po::value<size_t>()->default_value(1000), "Accesses to perform.");
  
  po::parsed_options parsed = po::command_line_parser(argc, argv).options(desc).run();
  
  po::variables_map vm;
  po::store(parsed, vm);
  po::notify(vm);
  if (vm.count("help")) {
    std::cout << desc << std::endl;
    exit(0);
  }
  size_t mem_size_small = vm["memory-size-small"].as<size_t>();
  size_t mem_size_large = vm["memory-size-large"].as<size_t>();
  int read_ratio = vm["read-ratio"].as<int>();
  size_t access_count = vm["access-count"].as<size_t>();
    
  int array_length = mem_size_large/sizeof(int);
  int * memory = (int *)calloc(array_length*sizeof(int), 1);

  if (memory == NULL) {
    fprintf(stderr, "Couldn't allocate memory.\n");
    exit(1);
  }

  for(size_t s = mem_size_small; s < mem_size_large; s*= 2) {
    pristine_machine();
    
    char name[1024];  // prepare two user-defined attributes for this run: vector size and clock speed
    sprintf(name, "%lu", s);
    
    start_timing(name, // Start timing
		 "MemoryRangeSize", name, // pass NULL-terminated list of user-defined key-value pairs
		 NULL);
    random_access(memory, s/sizeof(int), read_ratio, access_count);
    stop_timing(); // stop timing.
  }
  
  archlab_write_stats();
  
  return 0;
}

