#define _GNU_SOURCE             /* See feature_test_macros(7) */

#include<stdio.h>
#include<stdlib.h>
#include <sched.h>
#include<stdint.h>
#include<pthread.h>

inline static uint64_t fast_rand2(uint64_t * seed)
{
  uint64_t x = *seed;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *seed = x;
  return *seed << 32;
}

void * go(void*t);
int iters;
#define THREAD_COUNT 1

long int main(int argc, char *argv[]) {
  //cpu_set_t my_set;        /* Define your cpu_set bit mask. */
  //  CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
  //CPU_SET(0, &my_set);     /* set the bit that represents core 7. */
  //sched_setaffinity(0, sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to */
  
  long int sum;
  iters = atoi(argv[1])*10000;

  pthread_t *threads = (pthread_t*)malloc(8 * sizeof(pthread_t));
  for(int t= 0; t < THREAD_COUNT; t++) {
    pthread_create(&threads[t], NULL,go, 0);
  }
  for(int t = 0; t < THREAD_COUNT; t++) {
    void *r;
    pthread_join(threads[t], &r);
    sum += (long int)r;
  }
  return sum;

}

void *go(void*t) {
  uint64_t s = 4;
#define BOUNDS (1024*1024/sizeof(int))
  int * a = (int *) malloc(sizeof(int)*BOUNDS);
  int c;

  for(long int k = 0; k < BOUNDS; k++) {
    a[k] = fast_rand2(&s) % BOUNDS;
  }

  c = 0;
  long int sum;

  for(int i = 0; i < iters; i++) {
    int t = a[c];
    sum += t;
    c = t;
  }    
  
  return (void*)sum;
}
