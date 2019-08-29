#include "archlab.hpp"
#include <stdlib.h>
#include <getopt.h>
#include "microbenchmarks.h"
#include <iostream>
#include<string.h>
#include<unistd.h>
#include<pthread.h>

pthread_barrier_t prepare_barrier;
pthread_barrier_t go_barrier;
pthread_barrier_t done_barrier;


int threads;
volatile bool finished;

void *low_ilp(void*_a) {
  long int core = (long int)_a;
  theDataCollector->bind_this_thread_to_core(core);
  if (threads > 0) {
    pthread_barrier_wait(&prepare_barrier);
  }
  
  volatile int sum;
  int i = 0;
  while(!finished) {
    sum+=i;
    i++;
  }
  
  if (threads > 0) {
    pthread_barrier_wait(&done_barrier);
  }
  return NULL;
}

void *high_ilp(void*_a) {
  long int core = (long int)_a;
  theDataCollector->bind_this_thread_to_core(core);
  if (threads > 0) {
    pthread_barrier_wait(&prepare_barrier);
  }
  
  volatile int sum;
  int i = 0;
  while(!finished) {
    sum+=(i*3 + (i << 4) + (i >> 7) + i/13 + (i%9));
    i++;
  }
  
  if (threads > 0) {
    pthread_barrier_wait(&done_barrier);
  }
  return NULL;
}

int main(int argc, char *argv[]) {
  bool smt;
  int seconds;
  std::string t0mode, t1mode;
  archlab_add_option<int>("threads", threads, 2 ,  "How many threads to run: 1 or 2");
  archlab_add_flag("smt", smt, false , "Run them on the same physical core");
  archlab_add_option<int>("seconds", seconds, 1, "How many seconds to run for");
  archlab_add_option<std::string>("t0ilp", t0mode, "low", "Which function to run in t0");
  archlab_add_option<std::string>("t1ilp", t1mode, "low", "Which function to run in t1");
  
  archlab_parse_cmd_line(&argc, argv);
  pthread_t t0, t1;

  auto t0_func = t0mode == "low" ? low_ilp : high_ilp;
  auto t1_func = t1mode == "low" ? low_ilp : high_ilp;
  
  // All threads (including this one) will wait for preparation.  We
  // start execution by joining the prepare barrier. The workers will
  // all rush to go_barrier.  Then this thread synchs with them at the
  // done_barrier.

  if (threads > 0)  {
    pthread_barrier_init(&prepare_barrier, NULL, threads + 1);
    pthread_barrier_init(&done_barrier, NULL, threads + 1);
    pthread_create(&t0, NULL, t0_func, (void*)0);
  }
  
  if (threads == 2) 
    pthread_create(&t1, NULL, t1_func, (void*)(long)(smt ? 4 : 1));
  
  {
    ArchLabTimer timer;
    theDataCollector->pristine_machine();
    timer.
      attr("seconds", seconds).
      attr("thread_count", threads).
      attr("smt", smt).
      attr("t0-ilp", t0mode).
      attr("t1-ilp", t1mode).
      go();
    if (threads == 0) {
      t0_func((void*)1);
    } else {
      pthread_barrier_wait(&prepare_barrier);
      sleep(seconds);
      finished = true;
      pthread_barrier_wait(&done_barrier);
    }
  }
  
  archlab_write_stats();
  
  return 0;
}

