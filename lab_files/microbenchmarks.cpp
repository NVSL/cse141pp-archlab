#include"microbenchmarks.hpp"

int sink;

void random_access(int argc, char *argv[], void *_args)
{
  struct random_access_args *args = (struct random_access_args *)_args;
  uint64_t seed = 1;
  int s = 0;  
  int * array = args->memory;
  uint32_t read_ratio = args->read_ratio;
  size_t array_length = args->array_length;
  size_t access_count = args->access_count;

  
  for(unsigned int i= 0; i < access_count; i++) {
    uint64_t t = fast_rand2(&seed) % array_length;
      
    if(fast_rand2(&seed) % 100 > read_ratio) {
      array[t] = s;
    } else {
      s = array[t];
    }
  }
  sink = s;
}

void sequential_read(int argc, char *argv[], void *_args)
{
  struct sequential_read_args *args = (struct sequential_read_args *)_args;
  register int s = 0;
  register int * array = args->memory;
  register size_t array_length = args->array_length;
  register size_t access_count = args->access_count;
  register size_t stride = args->stride;

  for(unsigned int i = 0; i < access_count; i++) {
    s += array[(i*stride) % array_length];
  }
  
  sink = s;
}
