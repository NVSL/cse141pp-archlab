#include "archlab.h"
#include <stdio.h>

extern "C" {
 int not_unrolled(long int n, int a, int b);
}

int main(int argc, char *argv[]) {
  uint64_t count;
  archlab_add_si_option<uint64_t>("count",     count   , 100000  ,  "Iterations to run");
  printf("%ld\n", sizeof(long int));
  archlab_parse_cmd_line(&argc, argv);
  pristine_machine();               // reset the machine 
  start_timing("tag", "hello",      // Start timing.  Set an identifier 'tag' = 'hello'.  It'll appear along with the measurements in 'stats.csv'
	       NULL);
  uint64_t s = not_unrolled(count, 12, 20);
  stop_timing();                    // Stop timing.
  printf("Answer: %lu\n", s);
  archlab_write_stats();
  return 0;
}

