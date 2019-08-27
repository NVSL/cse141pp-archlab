#include "archlab.h"
#include <stdio.h>

extern "C" {
  int go(long int count, long int A, long int B);

}


int main(int argc, char *argv[]) {
  uint64_t count;
  long int A, B;
  archlab_add_si_option<uint64_t>("count",     count   , 100000,  "Iterations to run");
  archlab_add_si_option<int64_t>("A",     A   , 0,  "Parameter A");
  archlab_add_si_option<int64_t>("B",     B   , 0,  "Parameter B");
  printf("%ld\n", sizeof(long int));
  archlab_parse_cmd_line(&argc, argv);
  pristine_machine();               // reset the machine 
  start_timing("tag", "hello",      // Start timing.  Set an identifier 'tag' = 'hello'.  It'll appear along with the measurements in 'stats.csv'
	       NULL);

  archlab_start_quick();
  uint64_t s = go(count, A, B);
  archlab_stop_quick();
  stop_timing();                    // Stop timing.
  printf("Answer: %lu\n", s);
  archlab_write_stats();
  return 0;
}

