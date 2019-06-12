#include "archlab.h"
#include <stdio.h>

int main(int argc, char *argv[]) {
  archlab_parse_cmd_line(&argc, argv);
  pristine_machine();               // reset the machine 
  start_timing("tag", "hello",      // Start timing.  Set an identifier 'tag' = 'hello'.  It'll appear along with the measurements in 'stats.csv'
	       NULL);
  printf("hello world!\n");
  stop_timing();                    // Stop timing.
  archlab_write_stats();
  printf("Now, `cat stats.csv` will show you the results.\n");
  printf("Try `./hello_world.exe --engine papi --stat PAPI_L2_DCA --stat PAPI_TOT_CYC --stat PAPI_TOT_INS` to gather some actual measurements.\n");
  return 0;
}

