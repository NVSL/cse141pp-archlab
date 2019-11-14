#include "archlab.h"
#include <stdio.h>

// THis does nothing, but if archlab doesn't work, it'll fail so we can check for whether a given set of command line args works.
int main(int argc, char *argv[]) {
  archlab_parse_cmd_line(&argc, argv);
  pristine_machine();               // reset the machine 
  start_timing("tag", "hello",      // Start timing.  Set an identifier 'tag' = 'hello'.  It'll appear along with the measurements in 'stats.csv'
	       NULL);
  stop_timing();                    // Stop timing.
  return 0;
}

