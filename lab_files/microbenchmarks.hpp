#ifndef MICROBENCHMARKS_INCLUDED
#define MICROBENCHMARKS_INCLUDED

#include "lab_files/archlab.hpp"
#include <cstdlib>
#include<stdint.h>

struct random_access_args {
  int *memory;
  size_t array_length;
  uint32 read_ratio;
  size_t access_count;
};

void random_access(int argc, char *argv[], void *_args);

struct sequential_read_args {
  int *memory;
  size_t array_length;
  size_t access_count;
  size_t stride;
};

void sequential_read(int argc, char *argv[], void *_args);


#endif
