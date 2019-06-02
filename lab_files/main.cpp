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
#define N (L2_CACHE_SIZE/sizeof(double)/2)
  dp_args.A = (double *)malloc(N*sizeof(double));
  dp_args.B = (double *)malloc(N*sizeof(double));
  dp_args.len = N;
  
  for(uint i = 0; i < N; i++) {
    dp_args.A[i] = rand_double();
    dp_args.B[i] = rand_double();
  }
  naive(argc, argv, &dp_args);
#if (0)
  double correct = dp_args.sum;


  start_timing("warm", NULL);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  stop_timing();
  
  pristine_machine();
  
  start_timing("flushed", NULL);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  stop_timing();
  
  start_timing("reheated", NULL);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  stop_timing();
  
  start_timing("reheated_again", NULL);
  go(argc, argv, &dp_args);
  if (correct != dp_args.sum) {
    std::cout << "Incorrect output." << std::endl;
  }
  stop_timing();
#endif
  
  {
#define SIZE_COUNT 4
#define SIZE_BASE (4*MB)

#define ITERATIONS 10
    
    struct dot_product_args dp_args;
    dp_args.A = (double *)malloc((SIZE_BASE << SIZE_COUNT)*sizeof(double));
    dp_args.B = (double *)malloc((SIZE_BASE << SIZE_COUNT)*sizeof(double));

#define CPU_FREQUENCY_COUNT
    int cpu_frequencies[] = {
      3500,
      3100,
      2900,
      2700,
      2500,
      2300,
      2100,
      2000,
      1800,
      1600,
      1400,
      1200,
      1000,
      800};

    for(unsigned int j = 0; j < sizeof(cpu_frequencies)/sizeof(cpu_frequencies[0]); j++) {
      
      for(int i = 0; i < SIZE_COUNT; i++) {
	int size = SIZE_BASE << i;
	dp_args.len = size;
	pristine_machine();
	set_cpu_clock_frequency(cpu_frequencies[j]);
	char name[1024];
	sprintf(name, "%d", size);
	char clock[1024];
	sprintf(clock, "%dMHz", cpu_frequencies[j]);
	start_timing(name,
		     "VectorSize", name,
		     "ClockSpeed", clock,
		     NULL);
	for(int k = 0; k < ITERATIONS; k++) {
	  go(argc, argv, &dp_args);
	}
	stop_timing();
      }
    }
  }
  write_csv(stats_filename);
  return 0;
}	

