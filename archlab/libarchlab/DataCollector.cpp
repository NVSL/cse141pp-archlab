#include "archlab.h"
#include "DataCollector.hpp"
#include <iostream>
#include <cstring>
#include <json.hpp>
#include <stdlib.h>
#include <sstream>      // std::stringstream
#include <time.h>
#include <fcntl.h>
#include <stdarg.h>
#include <sys/types.h>
#include <unistd.h>
#include <fstream>
#include <sys/types.h>
#include <sys/stat.h>
#include <cache_control/cache_control.h>
#include <sys/ioctl.h>
#include <sched.h>

// for convenience
using json = nlohmann::json;


#define NAME_KEY "Name"

void DataCollector::init()
{
  pristine_machine();
  srand(time(0));
  // Bind the current process to core 0.
  cpu_set_t my_set;        /* Define your cpu_set bit mask. */
  CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
  CPU_SET(0, &my_set);     /* set the bit that represents core 7. */
  sched_setaffinity(getpid(), sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to */
                                                    /* the defined mask, i.e. only 7. */
  // Disable turboboost on core 0
  // https://askubuntu.com/questions/619875/disabling-intel-turbo-boost-in-ubuntu
  /*int r = system("/usr/sbin/wrmsr -p0 0x1a0 0x4000850089 >/dev/null");
  if (r != 0) {
    std::cerr << "Couldn't disable turbo boost." << std::endl;
    exit(1);
    }*/
}


void DataCollector::track_stat(const std::string  & stat)
{
  if (stat != "ARCHLAB_WALL_TIME") {
    unknown_stat(stat);
  }
}

void DataCollector::clear_tracked_stats() {
}

void DataCollector::start_timing(const char * name, json & kv)
{
  MeasurementInterval *n = newMeasurementInterval();
  
  n->kv = kv;
  n->kv[NAME_KEY] = name;

  std::cerr << "Starting " << name << " at " << wall_time() <<  std::endl;
  if (current_interval) {
    std::cerr << "You are already timing something (\"" << current_interval->kv[NAME_KEY] << "\").  You can't time something else." << std::endl;
    exit(1);
  }
  enqueue_interval(n);
  current_interval = n;
  n->start();
}

void DataCollector::stop_timing()
{

  if (!current_interval) {
    std::cerr << "You are not currently timing anything." << std::endl;
    exit(1);
  }
  
  current_interval->stop();
  current_interval = NULL;
}

json MeasurementInterval::build_json()
{
  kv["WallTime"] = _end->time - _start->time;
  return kv;
}

void MeasurementInterval::add_string(char * name, char * value)
{
  add_field<std::string>(name, std::string(value));
}

void MeasurementInterval::add_double(char * name, double value)
{
  add_field<double>(name, value);
}

void MeasurementInterval::start()
{
  _start->measure();
}

void MeasurementInterval::stop()
{
  _end->measure();
}

std::string MeasurementInterval::build_csv()
{
  json j = build_json();

  std::stringstream out;

  out << kv[NAME_KEY] <<  ",";
  for (auto& el : kv.items()) {
    if (el.key() == NAME_KEY) continue;
    out << el.value() << ",";
  }

  out << "\n";
  return out.str();
}

std::string MeasurementInterval::build_csv_header()
{
  json j = build_json();

  std::stringstream out;

  out << NAME_KEY <<  ",";
  for (auto& el : kv.items()) {
    if (el.key() == NAME_KEY) continue;
    out << el.key() << ",";
  }

  out << "\n";
  return out.str();
}

json DataCollector::build_json() {
  json j;

  for(auto i = stored_intervals.begin();
      i != stored_intervals.end();
      i++) {
    j[(*i)->kv[NAME_KEY].get<std::string>()] = (*i)->kv;
  }
  return j;
}

void DataCollector::write_json(std::ostream & out)
{
  out << build_json().dump(4) << std::endl;  
}

void DataCollector::write_json(const char * filename)
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate())  {
    std::cerr << "Opening " << filename << " failed." << std::endl;
    exit(1);
  }
  write_json(out);
  out.close();
}



void DataCollector::write_csv(const char * filename)
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate())  {
    std::cerr << "Opening " << filename << " failed." << std::endl;
    exit(1);
  }
  write_csv(out);
  out.close();
}
	       
void DataCollector::write_csv(std::ostream & out)
{
  if (stored_intervals.size()) {
    out << stored_intervals[0]->build_csv_header();
    for(auto i = stored_intervals.begin(); i != stored_intervals.end(); i++) {
      out << (*i)->build_csv();
    }
  }
}

void DataCollector::pristine_machine()
{
  flush_caches();
  set_cpu_clock_frequency(3500);
}

void DataCollector::set_cpu_clock_frequency(int MHz) {
  char buf[1024];
  sprintf(buf, "/usr/bin/cpupower frequency-set --freq %dMHz > /dev/null", MHz);
  int r = system(buf);
  if (r != 0) {
    std::cerr << "Couldn't set cpu frequency to " << MHz << "MHz (" << r << ")" << std::endl;
    exit(1);
  }
}

void DataCollector::flush_caches() {
  
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
  
}


void DataCollector::unknown_stat(const std::string & s) {
  std::cerr << collector_name << " engine cannot record '" << s << "'. Ignoring." << std::endl;
}
