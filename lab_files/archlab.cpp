#include <iostream>
#include <cpucounters.h>
#include "archlab.hpp"
#include <cstring>
#include <lab_files/cache_control/cache_control.h>
#include <sys/ioctl.h>
// from https://github.com/nlohmann/json
#include <json.hpp>
#include <stdlib.h>
#include <sstream>      // std::stringstream
#include<time.h>
#include <stdarg.h>
#include <sys/types.h>
#include "PCMDataCollector.hpp"
#include "PAPIDataCollector.hpp"
#include "PINDataCollector.hpp"
DataCollector *theDataCollector = NULL;

void archlab_init(int collector)
{
  if (collector == ARCHLAB_COLLECTOR_PCM) {
    theDataCollector = new PCMDataCollector();
  } else if (collector == ARCHLAB_COLLECTOR_PAPI) {
    theDataCollector = new PAPIDataCollector();
  } else if (collector == ARCHLAB_COLLECTOR_PIN) {
    theDataCollector = new PINDataCollector();
  } else if (collector == ARCHLAB_COLLECTOR_NONE) {
    theDataCollector = new DataCollector();
  } else {
    std::cerr << "Unknown data collector: " << collector << std::endl;
    exit(0);
  }
  theDataCollector->init();
}

void papi_track_event(int event)
{
  PAPIDataCollector *dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  dc->track_event(event);
}
void papi_clear_events()
{
  PAPIDataCollector *dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  dc->clear_events();
}

void pin_track_event(int event)
{
  PINDataCollector *dc = dynamic_cast<PINDataCollector*>(theDataCollector);
  dc->track_event(event);
}

void start_timing(const char * name...)
{
  json kv;

  va_list args;
  va_start(args, name);

  while (char* k = va_arg(args, char *)) {
    //std::cerr << k << std::endl;
    char * v = va_arg(args, char *);
    //    std::cerr << v << std::endl;
    if (v == NULL) {
      std::cerr << "Missing value for last key-value pair in start_timing." << std::endl;
      exit(1);
    }
    kv[k] = v;
  }

  va_end(args);

  theDataCollector->start_timing(name, kv);
}

void stop_timing()  {theDataCollector->stop_timing();}
void write_csv(const char * filename) {theDataCollector->write_csv(filename);}

int flush_caches() {
  int fd = open("/dev/cache_control", O_RDWR);
  if (fd == -1) {
    std::cerr << "Couldn't open '/dev/cache_control' to flush caches: " << strerror(errno) << std::endl;
    exit(1);

  }
  int r = ioctl(fd, CACHE_CONTROL_FLUSH_CACHES);
  if (r == -1) {
    std::cerr << "Flushing caches failed: " << strerror(errno) << std::endl;
    exit(1);
  }
  return 1;
}

int pristine_machine() {
  flush_caches();
  set_cpu_clock_frequency(3500);
  return 1;
}

int set_cpu_clock_frequency(int mhz)
{
  char buf[1024];
  sprintf(buf, "/usr/bin/cpupower frequency-set --freq %dMHz > /dev/null", mhz);
  int r = system(buf);
  if (r != 0) {
    std::cerr << "Couldn't set cpu frequency to " << mhz << "MHz (" << r << ")" << std::endl;
    exit(1);
  }
  return 1;
}


