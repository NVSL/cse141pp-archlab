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
#include <sys/types.h>
#include <sys/wait.h> 
#include <sys/sysinfo.h>



// for convenience
using json = nlohmann::json;



void DataCollector::init()
{
  pristine_machine();
  srand(time(0));
  // Bind the current process to core 0.
  cpu_set_t my_set;        /* Define your cpu_set bit mask. */
  CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
  CPU_SET(0, &my_set);     /* set the bit that represents core 7. */
  sched_setaffinity(getpid(), sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to the defined mask, i.e. only 7. */
  
  // Disable turboboost on core 0
  // https://askubuntu.com/questions/619875/disabling-intel-turbo-boost-in-ubuntu
  /*int r = system("/usr/sbin/wrmsr -p0 0x1a0 0x4000850089 >/dev/null");
  if (r != 0) {
    std::cerr << "Couldn't disable turbo boost." << std::endl;
    exit(1);
    }*/
}


void DataCollector::init(bool do_cpu_affinity) 
{
  if (do_cpu_affinity) {
    // Bind the current process to core 0.
    cpu_set_t my_set;        /* Define your cpu_set bit mask. */
    CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
    CPU_SET(0, &my_set);     /* set the bit that represents core 7. */
    sched_setaffinity(getpid(), sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to */
  }
  pristine_machine();
  srand(time(0));
}


int DataCollector::run_child(char *exec, char *argv[])
{
  pid_t child_pid;
  if( (child_pid = fork()) == 0 )  //Purposeful assignment, not comparison
    {
      int r = execvp(exec, argv);
      std::cerr << "Exec returned\n";
      if (r == -1) {
	std::cerr << "Couldn't exec '" << exec << "': " << strerror(errno) << "\n";
	exit(1);
      }
    }
  else if( child_pid < 0 )
    {
      fprintf( stderr, "Failed to create child process. Exiting...\n" );
      exit(1);
    }
  
  int status;
  //usleep( (useconds_t) 5000 ); Not sure why leo had this in here.
  pid_t r = waitpid(child_pid, &status,0);
  if (r == -1) {
    std::cerr << "Couldn't wait for child to exit. I'm exiting...\n";
    exit(1);
  }

  return WEXITSTATUS(status);
}

void DataCollector::get_usage(std::ostream & f) {
}

void DataCollector::track_stat(const std::string  & stat)
{
  if (stat != "ARCHLAB_WALL_TIME") {
    unknown_stat(stat);
  }
}

void DataCollector::clear_tracked_stats() {
}

void DataCollector::add_default_kv(const std::string & key, const std::string & value)
{
	default_kv[key] = value;
}

void DataCollector::start_timing(json & kv)
{
  MeasurementInterval *n = newMeasurementInterval();
  n->kv = default_kv;
  n->kv.merge_patch(kv);
  if (current_interval) {
    std::cerr << "You are already timing something.  You can't time something else." << std::endl;
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

  for (auto& el : kv.items()) {
    out << el.value() << ",";
  }

  out << "\n";
  return out.str();
}

std::string MeasurementInterval::build_csv_header()
{
  json j = build_json();

  std::stringstream out;

  for (auto& el : kv.items()) {
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
    j.push_back((*i)->kv);
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
  enable_prefetcher();
  set_cpu_clock_frequency(cpu_frequencies[0]);
  
}

void DataCollector::set_cpu_clock_frequency(int MHz) {
  if (MHz == -1) {
    return;
  }
  
  char buf[1024];
  sprintf(buf, "/usr/bin/cpupower frequency-set --freq %dMHz > /dev/null", MHz);
  int r = system(buf);
  if (r != 0) {
    std::cerr << "Couldn't set cpu frequency to " << MHz << "MHz (" << r << ")" << std::endl;

  }
}

void DataCollector::enable_prefetcher(int flags) {

  int cpus = get_nprocs_conf();
  char buf[1024];
  for(int i = 0;i < cpus; i++) {
    //https://software.intel.com/en-us/articles/disclosure-of-hw-prefetcher-control-on-some-intel-processors
    sprintf(buf, "wrmsr -p %d 0x1a4 %d", i, ~flags & 15); // in the register, a 1 disables the register.  So invert and mask out the highorder bits.

    //std::cerr << buf << "\n";
    int r = system(buf);
    if (r != 0) {
      std::cerr << "Couldn't set prefetcher flags or core " << i << " to " << flags << "\n";
    }
  }
}

void DataCollector::disable_prefetcher() {
  enable_prefetcher(0);
}

void DataCollector::flush_caches() {

  if( access( "/dev/cache_control", R_OK|W_OK ) != 0) {
    std::cerr << "Couldn't open '/dev/cache_control'.  Not flushing caches.\n";
    return;
  }  
  
  int fd = open("/dev/cache_control", O_RDWR);
  if (fd == -1) {
    std::cerr << "Couldn't open '/dev/cache_control' to flush caches: " << strerror(errno) << std::endl;
    return;
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
