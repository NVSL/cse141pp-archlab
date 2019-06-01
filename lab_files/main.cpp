#include "lab_files/archlab.hpp"
#include <cstdlib>
#include <getopt.h>

#include "lab.h"

// from https://github.com/nlohmann/json
extern "C" {
  int go(int argc, char *argv[], void *args);
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

void naive(int argc, char * argv[], void* _args) {
  struct dot_product_args * args = (struct dot_product_args*)_args;
  double * A = args->A;
  double * B = args->B;
  int len = args->len;
  
  double sum = 0.0; 
  for(int i = 0; i < len; i++) {
    sum += A[i] * B[i];
  }

  args->sum =sum;
}

int main(int argc, char *argv[]) {

  // Boiler plate
  
  parse_cmd_line(argc, argv);
  archlab_init();
  
  struct dot_product_args dp_args;
#define L1_CACHE_SIZE (128*KB)
#define L2_CACHE_SIZE (1*MB)
#define L3_CACHE_SIZE (8*MB)
#define N (L3_CACHE_SIZE/sizeof(double)/2)
  dp_args.A = (double *)malloc(N*sizeof(double));
  dp_args.B = (double *)malloc(N*sizeof(double));
  dp_args.len = N;
  
  for(uint i = 0; i < N; i++) {
    dp_args.A[i] = rand_double();
    dp_args.B[i] = rand_double();
  }
  naive(argc, argv, &dp_args);
  double correct = dp_args.sum;
  
  struct Measurement one;
  take_measurement(&one);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  pristine_machine();
  struct Measurement two;
  take_measurement(&two);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  struct Measurement three;
  take_measurement(&three);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  struct Measurement four;
  take_measurement(&four);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  struct Measurement five;
  take_measurement(&five);
  
  write_system_config(system_config_filename);
  write_run_stats(stats_filename, &one, &four);
  write_run_stats("warm.json", &one, &two);
  write_run_stats("cold.json", &two, &three);
  write_run_stats("reheated.json", &three, &four);
  write_run_stats("rereheated.json", &four, &five);
  return 0;
}	

