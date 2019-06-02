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

#include <sched.h>

// for convenience
using json = nlohmann::json;

#define NAME_KEY "Name"

void archlab_init()
{
  PCM::getInstance()->program();
  pristine_machine();
  srand(time(0));

  // Bind the current process to core 0.
  cpu_set_t my_set;        /* Define your cpu_set bit mask. */
  CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
  CPU_SET(0, &my_set);     /* set the bit that represents core 7. */
  sched_setaffinity(0, sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to */
                                                    /* the defined mask, i.e. only 7. */
  // Disable turboboost on core 0
  // https://askubuntu.com/questions/619875/disabling-intel-turbo-boost-in-ubuntu
  int r = system("/usr/sbin/wrmsr -p0 0x1a0 0x4000850089 >/dev/null");
  if (r != 0) {
    std::cerr << "Couldn't disable turbo boost." << std::endl;
    exit(1);
  }
}

template<class T>
void measurement_interval_add_field(struct MeasurementInterval * m, char * name, const T & v) {
  m->kv[name] = v;
}

void measurement_interval_add_string(struct MeasurementInterval * m, char * name, char * value)
{
  measurement_interval_add_field<char *>(m, name, value);
}

void measurement_interval_add_double(struct MeasurementInterval * m, char * name, double value)
{
  measurement_interval_add_field<double>(m, name, value);
}

void measurement_interval_start(struct MeasurementInterval * m)
{
  take_measurement(&m->start);
}

void measurement_interval_stop(struct MeasurementInterval * m)
{
  take_measurement(&m->end);
}

std::vector<struct MeasurementInterval* > stored_intervals;
struct MeasurementInterval * current_interval = NULL;

void store_measurement_interval_for_output(struct MeasurementInterval * m)
{
  stored_intervals.push_back(m);
}

void start_timing(const char * name...)
{
  std::cerr << "Starting " << name << " at " << wall_time() <<  std::endl;
  if (current_interval) {
    std::cerr << "You are already timing something (\"" << current_interval->kv[NAME_KEY] << "\").  You can't time something else." << std::endl;
    exit(1);
  }

  struct MeasurementInterval *n = new MeasurementInterval;
  n->kv[NAME_KEY] = name;

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
    n->kv[k] = v;
  }

  va_end(args);
  
  store_measurement_interval_for_output(n);
  current_interval = n;
  measurement_interval_start(n);
}

void stop_timing()
{
  if (!current_interval) {
    std::cerr << "You are not currently timing anything." << std::endl;
    exit(1);
  }
  
  measurement_interval_stop(current_interval);
  current_interval = NULL;
}

void take_measurement(struct Measurement * measurement)
{
  measurement->time = wall_time();
  PCM::getInstance()->getAllCounterStates(measurement->pcm_system_counter_state,
					  measurement->pcm_socket_counter_state,
					  measurement->pcm_core_counter_state);
}

#define PCM_MEASUREMENT_STAT_FIELDS \
  MEASUREMENT_STAT_FIELD(IPC)\
  MEASUREMENT_STAT_FIELD(L3CacheHitRatio)\
  MEASUREMENT_STAT_FIELD(L3CacheMisses)\
  MEASUREMENT_STAT_FIELD(L3CacheHits)\
  MEASUREMENT_STAT_FIELD(L2CacheHitRatio)\
  MEASUREMENT_STAT_FIELD(L2CacheHits)\
  MEASUREMENT_STAT_FIELD(L2CacheMisses)\
  MEASUREMENT_STAT_FIELD(AverageFrequency)
  //  MEASUREMENT_STAT_FIELD(BytesReadFromMC)

#define CUSTOM_MEASUREMENT_STAT_FIELDS \
  MEASUREMENT_STAT_FIELD(WallTime)

#define MEASUREMENT_STAT_FIELDS \
  CUSTOM_MEASUREMENT_STAT_FIELDS\
  PCM_MEASUREMENT_STAT_FIELDS

#define SYSTEM_STAT_FIELDS \
  SYSTEM_STAT_FIELD(NumCores)\
  SYSTEM_STAT_FIELD(NumSockets)\
  SYSTEM_STAT_FIELD(SMT)\
  SYSTEM_STAT_FIELD(NominalFrequency)\
  SYSTEM_STAT_FIELD(CPUModel)\
  SYSTEM_STAT_FIELD(OriginalCPUModel)\
  SYSTEM_STAT_FIELD(MaxIPC)

#define ALL_FIELDS \
  CUSTOM_MEASUREMENT_STAT_FIELDS\
  SYSTEM_STAT_FIELDS\
  PCM_MEASUREMENT_STAT_FIELDS

json measurement_interval_build_json(struct MeasurementInterval * mi)
{
  json j = mi->kv;
  
#define MEASUREMENT_STAT_FIELD(s) j[#s] = get##s(mi->start.pcm_core_counter_state[0], mi->end.pcm_core_counter_state[0]);
PCM_MEASUREMENT_STAT_FIELDS
#undef MEASUREMENT_STAT_FIELD

#define SYSTEM_STAT_FIELD(s) j[#s] = PCM::getInstance()->get##s();
SYSTEM_STAT_FIELDS
#undef SYSTEM_STAT_FIELD

  j["WallTime"] = mi->end.time - mi->start.time;
  
  return j;  
}

std::string measurement_interval_build_csv(struct MeasurementInterval *mi)
{
  json j = measurement_interval_build_json(mi);

  std::stringstream out;

  out << mi->kv[NAME_KEY] <<  ",";
  for (auto& el : mi->kv.items()) {
    if (el.key() == NAME_KEY) continue;
    out << el.value() << ",";
  }
  
#define MEASUREMENT_STAT_FIELD(s) out << j[#s] << ",";
#define SYSTEM_STAT_FIELD(s)      out << j[#s] << ",";
  ALL_FIELDS;
#undef MEASUREMENT_STAT_FIELD
#undef SYSTEM_STAT_FIELD
  out << "\n";
  return out.str();
}

std::string measurement_interval_build_csv_header(struct MeasurementInterval *mi)
{
  json j = measurement_interval_build_json(mi);

  std::stringstream out;

  out << NAME_KEY <<  ",";
  for (auto& el : mi->kv.items()) {
    if (el.key() == NAME_KEY) continue;
    out << el.key() << ",";
  }
  
  
#define MEASUREMENT_STAT_FIELD(s) out << #s << ",";
#define SYSTEM_STAT_FIELD(s)      out << #s << ",";
  ALL_FIELDS;
#undef MEASUREMENT_STAT_FIELD
#undef SYSTEM_STAT_FIELD
  out << "\n";
  return out.str();
}

void measurement_interval_write_json(std::ostream & out,
				     struct MeasurementInterval * mi)
{
  out << measurement_interval_build_json(mi).dump(4) << std::endl;  
}


void write_run_csv(std::ostream & out,
		   struct MeasurementInterval * mi)
{
  out << measurement_interval_build_csv_header(mi);
  out << measurement_interval_build_csv(mi);
}

void write_csv(const char * filename)
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
	       
void write_csv(std::ostream & out)
{
  if (stored_intervals.size()) {
    out << measurement_interval_build_csv_header(stored_intervals[0]);
    for(auto i = stored_intervals.begin(); i != stored_intervals.end(); i++) {
      out << measurement_interval_build_csv(*i);
    }
  }
}
	       


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
