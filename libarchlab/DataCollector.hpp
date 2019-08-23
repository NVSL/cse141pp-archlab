#ifndef DATA_COLLECTOR_INCLUDED
#define DATA_COLLECTOR_INCLUDED
#include<stdint.h>
#include"archlab.hpp"
#include <json.hpp>
using json = nlohmann::json;
  
class Measurement {
public:
  double time;
  virtual void measure() { time = wall_time();}; 
  virtual ~Measurement() {}
};

class DataCollector;

class MeasurementInterval {
protected:
  json kv;
  Measurement * _start;
  Measurement * _end;
  friend DataCollector;
  explicit MeasurementInterval(Measurement*s, Measurement *e): _start(s), _end(e) {} 
public:
  MeasurementInterval(): _start(new Measurement), _end(new Measurement) {}
  
  virtual ~MeasurementInterval() {
    delete _start;
    delete _end;
  }
  
  template<class T>
  void add_field(char * name, const T & v) {
    kv[name] = v;
  }
  
  void add_string(char * name, char * value);
  void add_double(char * name, double value);
  virtual void start();
  virtual void stop();
  virtual json build_json();
  std::string build_csv();
  std::string build_csv_header();

};

class DataCollector {
  std::vector<MeasurementInterval* > stored_intervals;
  std::string stats_filname;
  const std::string collector_name;
  MeasurementInterval * current_interval;
	json default_kv;

protected:
  virtual MeasurementInterval * newMeasurementInterval() {return new MeasurementInterval();}
  explicit DataCollector(const std::string &name): collector_name(name), current_interval(NULL) {}
public:

  // https://software.intel.com/en-us/articles/disclosure-of-hw-prefetcher-control-on-some-intel-processors
  enum {PREFETCH_L2 = 1,
	PREFETCH_L2_PAIR = 2,
	PREFETCH_L1_NEXT_LINE = 4,
	PREFETCH_L1_SEQ_HIST = 8};

  DataCollector() : DataCollector("Native") {}
  
  
  virtual void init();
  virtual void start_timing(json & kv);
  virtual void stop_timing();
  virtual void pristine_machine();
  virtual void enable_prefetcher(int flags = 15);  // flags should be some |'d combination of the PREFETCH_* enums above.
  virtual void disable_prefetcher();
  virtual void flush_caches();
  virtual void set_cpu_clock_frequency(int MHz);

  virtual void track_stat(const std::string &stat);
  virtual void clear_tracked_stats();
  virtual void get_usage(std::ostream & f);
  virtual int  run_child(char *exec, char *argv[]);
  
  void set_stats_filename(const std::string &s) {stats_filname = s;}
  void enqueue_interval(MeasurementInterval *mi) {
    stored_intervals.push_back(mi);
    current_interval = mi;
  }

  json build_json();
  void write_json(const char * filename);
  void write_json(std::ostream & out);
  void write_csv(const char * filename);
  void write_csv(std::ostream & out);
  void write_stats() {write_csv(stats_filname.c_str());}
  void add_default_kv(const std::string & key, const std::string & value);

  const std::string & get_name() const {return collector_name;} 
  void unknown_stat(const std::string & s);
};

#endif
