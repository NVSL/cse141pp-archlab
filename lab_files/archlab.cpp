#include <iostream>
#include <cpucounters.h>
#include "archlab.hpp"
#include <cstring>
#include <lab_files/cache_control/cache_control.h>
#include <sys/ioctl.h>
// from https://github.com/nlohmann/json
#include <json.hpp>
#include <stdlib.h>
#include<time.h>

// for convenience
using json = nlohmann::json;

void archlab_init()
{
  PCM::getInstance()->program();
  srand(time(0));
}

void write_system_config(const char * filename)
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate()) 
    std::cerr << "Opening " << filename << " failed." << std::endl;
  write_system_config(out);
  out.close();
}

void write_system_config(std::ostream & out)
{
#define GET_SYS_STAT(j, s) j[#s] = PCM::getInstance()->get##s()
  json system;
  GET_SYS_STAT(system, NumCores);
  GET_SYS_STAT(system, NumSockets);
  GET_SYS_STAT(system, SMT);
  GET_SYS_STAT(system, NominalFrequency);
  GET_SYS_STAT(system, CPUModel);
  GET_SYS_STAT(system, OriginalCPUModel);
  GET_SYS_STAT(system, MaxIPC);
  out << system.dump(4) << std::endl;  
}

void write_run_stats(const char * filename,
		     struct Measurement * before,
		     struct Measurement * after)  
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate()) 
    std::cerr << "Opening " << filename << " failed." << std::endl;

  write_run_stats(out, before, after);
  out.close();
}

void take_measurement(struct Measurement * measurement)
{
  measurement->time = wall_time();
  PCM::getInstance()->getAllCounterStates(measurement->pcm_system_counter_state,
					  measurement->pcm_socket_counter_state,
					  measurement->pcm_core_counter_state);
}

void write_run_stats(std::ostream & out,
		     struct Measurement * before,
		     struct Measurement * after)
{

#define GET_RUN_STAT(j, s, before, after) j[#s] = get##s(before, after)

  json j;
  GET_RUN_STAT(j, IPC,
	       before->pcm_system_counter_state,
	       after->pcm_system_counter_state);
  GET_RUN_STAT(j, L3CacheHitRatio,
	       before->pcm_system_counter_state,
	       after->pcm_system_counter_state);
  GET_RUN_STAT(j, L2CacheHitRatio,
	       before->pcm_system_counter_state,
	       after->pcm_system_counter_state);
  GET_RUN_STAT(j, BytesReadFromMC,
	       before->pcm_system_counter_state,
	       after->pcm_system_counter_state);
  j["wall_time"] = after->time - before->time;
  
  out << j.dump(4) << std::endl;  
}


int flush_caches() {
  int fd = open("/dev/cache_control", O_RDWR);
  if (fd == -1) {
    std::cerr << "Couldn't open '/dev/cache_control' to flush caches: " << strerror(errno) << std::endl;
    return 0;
  }
  int r = ioctl(fd, CACHE_CONTROL_FLUSH_CACHES);
  if (r == -1) {
    std::cerr << "Flushing caches failed: " << strerror(errno) << std::endl;
    return 0;
  }
  return 1;
}

int pristine_machine() {
  return flush_caches();
}

int set_cpu_clock_frequency(int mhz)
{
  char buf[1024];
  sprintf(buf, "/usr/bin/cpupower frequency-set --freq %dMHz",mhz);
  int r = system(buf);
  if (r != 0) {
    std::cerr << "Couldn't set cpu frequency to " << mhz << "MHz (" << r << ")" << std::endl;
    return 0;
  }
  return 1;
}
