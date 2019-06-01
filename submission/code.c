#include <stdio.h>
#include <stdlib.h>
#include "lab_files/lab.h"
#define N (128ll*4096ll*4096ll)
#define ITERS 100


void go(int argc, char * argv[], void* _args) {
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
