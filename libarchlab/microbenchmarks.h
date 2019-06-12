#ifndef MICROBENCHMARKS_INCLUDED
#define MICROBENCHMARKS_INCLUDED

#include <stdlib.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
  
  void random_access(register int * array, register size_t len, register uint32_t read_ratio, register size_t access_count);

struct sequential_read_args {
  int *memory;
  size_t array_length;
  size_t access_count;
  size_t stride;
};

void sequential_read(void *_args);

  void nop();
  void do_sleep(int seconds);
  
#ifdef __cplusplus
}
#endif

#endif
