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
  void start();
  void stop();
  virtual json build_json();
  std::string build_csv();
  std::string build_csv_header();

};

class DataCollector {
  std::vector<MeasurementInterval* > stored_intervals;
  MeasurementInterval * current_interval;
  
protected:
  virtual MeasurementInterval * newMeasurementInterval() {return new MeasurementInterval();}
  
public:
  virtual void init();
  void start_timing(const char * name, json & kv);
  void stop_timing();

  void enqueue_interval(MeasurementInterval *mi) {
    stored_intervals.push_back(mi);
    current_interval = mi;
  }

  json build_json();
  void write_json(const char * filename);
  void write_json(std::ostream & out);
  void write_csv(const char * filename);
  void write_csv(std::ostream & out);

};

#endif
