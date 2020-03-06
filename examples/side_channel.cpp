#include "archlab.hpp"
#include <stdlib.h>
#include <getopt.h>
#include <iostream>
#include<string.h>
#include<unistd.h>
#include<bitset>
#include <boost/program_options.hpp>
namespace po = boost::program_options;
#define SIZE_BASE ((4<<16)*KB)
#define SIZE_COUNT 1
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <cache_control/cache_control.h>
#include<pthread.h>

volatile int sink = 0;

uint64_t rdtsc(){
	unsigned int lo,hi;
	__asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
	return ((uint64_t)hi << 32) | lo;
}
uint64_t cache_size;
uint64_t target_lines;

char * array;

void * thread_sender(void * arg)
{
	while (true) {
		for(uint i = 0; i < 1000; i++) {
			for(uint j = 0; j < target_lines; j++) {
				array[j*cache_size]++;
			}
		}
		//std::cerr << "Sleeping" << std::endl;
		sleep(1);
		//std::cerr << "Waking" << std::endl;
	}
	return NULL;
}

void * thread_receiver(void * arg)
{
	double start = wall_time();
	//std::cerr << "Start = " << start << "\n";
	while(true) {
		
		uint64_t before = rdtsc();
		for(uint i = 0; i < 100; i++) {
			for(uint j = 0; j < target_lines; j++) {
				array[j*cache_size]++;
			}
		}
		double now = wall_time();

		std::cerr << (now - start) << " " << (rdtsc() - before)/(target_lines + 100 + 0.0) << std::endl;
	}
	return NULL;
}

int main(int argc, char *argv[]) {
	//uint64_t seed = 0xdeadbeafabad1dea;
	archlab_add_si_option<uint64_t>("cache-size",  cache_size, 32*KB ,  "Cache size.");
	archlab_add_si_option<uint64_t>("target-lines",  target_lines, 16,  "Number of cache lines to target");
	//archlab_add_flag("enable-demo", enable_demo, false ,  "Run demos.");
	//archlab_add_flag("no-prefetch", disable_prefetcher, false ,  "Disable the HW prefetcher.");
		     
	archlab_parse_cmd_line(&argc, argv);

	array = (char*)malloc(cache_size * target_lines);

	pthread_t t1;
	pthread_t t2;
	
	pthread_create(&t1, NULL, thread_sender, NULL);
	pthread_create(&t2, NULL, thread_receiver, NULL);

	pthread_join(t2, NULL);
  
	return 0;
}

