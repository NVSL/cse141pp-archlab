#ifndef DATA_COLLECTOR_INCLUDED
#define DATA_COLLECTOR_INCLUDED
#include<stdint.h>
#include"archlab.hpp"
#include <json.hpp>
using json = nlohmann::json;
  
class Measurement {
public:
  float time;
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
protected:
  virtual MeasurementInterval * newMeasurementInterval() {return new MeasurementInterval();}
  explicit DataCollector(const std::string &name): collector_name(name), current_interval(NULL) {}
public:

  DataCollector() : DataCollector("Native") {}
  
  
  virtual void init();
  virtual void start_timing(const char * name, json & kv);
  virtual void stop_timing();
  virtual void pristine_machine();
  virtual void flush_caches();
  virtual void set_cpu_clock_frequency(int MHz);

  virtual void track_stat(const std::string &stat);
  virtual void clear_tracked_stats();
  virtual void get_usage(std::ostream & f);

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

  const std::string & get_name() const {return collector_name;} 
  void unknown_stat(const std::string & s);
};

#endif