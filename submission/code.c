#include <stdio.h>
#include <stdlib.h>
#include "lab_files/tools.h"

#define N (128*4*4096)
#define ITERS 100


double naive(double * A, double *B, int len) {
  double sum = 0.0; 
  for(int i = 0; i < len; i++) {
    sum += A[i] * B[i];
  }
  return sum;
}

int go(int argc, char *argv[]) {
  
  double *A = (double *)malloc(N*sizeof(double));
  double *B = (double *)malloc(N*sizeof(double));

  float last;
  float s = 0;

#define CHECK_TIME(f) do {					\
    last = wall_time();						\
    for(int j= 0; j < ITERS; j++) {				\
      s += f(A, B, N);						\
    }								\
    fprintf(stdout, #f": %f\n",  wall_time() - last);		\
  } while(0)
  
  
  CHECK_TIME(naive);

  if (s == 10) {
    return 0;
  } else {
    return 1;
  }
}
