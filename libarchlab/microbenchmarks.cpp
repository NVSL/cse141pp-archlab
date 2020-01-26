#include"microbenchmarks.h"
#include"archlab.h"
#include<unistd.h>

extern "C" {
  int sink;

  void random_access(register int * array, register size_t len, register uint32_t read_ratio, register size_t access_count)
  {
	  uint64_t seed = 1;
	  register int s = 0;  
	  
	  for(register unsigned int i= 0; i < access_count; i++) {
		  register uint64_t t = fast_rand2(&seed);// % len;
		  if(t % 100 > read_ratio) {
			  array[t % len] = s;
		  } else {
			  s = array[t %len];
		  }
	  }
	  sink = s;
  }

  void sequential_read(void *_args)
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

  void nop() {
  }

  void do_sleep(int seconds) {
    sleep(seconds);
  }

}
