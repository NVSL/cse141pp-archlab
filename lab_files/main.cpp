#include "lab_files/lab.hpp"
#include <cstdlib>
#include <getopt.h>

// from https://github.com/nlohmann/json
extern "C" {
  int go(int argc, char *argv[]);
}

char * system_config_filename = strdup("system.json");
char * stats_filename = strdup("stats.json");

void parse_cmd_line(int argc, char *argv[]) {
  int c;

  while (1) {
    static struct option long_options[] =
      {
	{"system-config", required_argument,       0, 'c'},
	{"stats-file",    required_argument,       0, 's'},
	{0, 0, 0, 0}
      };
    /* getopt_long stores the option index here. */
    int option_index = 0;
    
    c = getopt_long (argc, argv, "c:s:",
		     long_options, &option_index);
    
    /* Detect the end of the options. */
    if (c == -1)
      break;
    
    switch (c)
      {
      case 'c':
	system_config_filename = strdup(optarg);
	break;
      case 's':
	stats_filename = strdup(optarg);
	break;
      case '?':
	/* getopt_long already printed an error message. */
	break;

      default:
	abort ();
      }
  }
}

int main(int argc, char *argv[]) {
  parse_cmd_line(argc, argv);
  
  SystemCounterState before = getSystemCounterState();
  go(argc, argv);
  SystemCounterState after = getSystemCounterState();
  write_system_config(system_config_filename);
  write_run_stats(stats_filename, before, after);
  return 0;
}	

