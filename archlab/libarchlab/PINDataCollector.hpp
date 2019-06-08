#ifndef PIN_DATA_COLLECTOR_INCLUDED
#define PIN_DATA_COLLECTOR_INCLUDED

#include"DataCollector.hpp"

#define PIN_MAX_REGISTERS 32

extern char * archlab_pin_registers[];

class PINMeasurementInterval: public MeasurementInterval {
  uint64_t registers[PIN_MAX_REGISTERS];
public:
  void start();
  void stop();
  json build_json();
};

class PINDataCollector: public DataCollector {
  friend PINMeasurementInterval;

  std::vector<int> tracked_registers;
public:

  PINDataCollector() : DataCollector("PIN"){}
  MeasurementInterval * newMeasurementInterval() {return new PINMeasurementInterval();}

  void track_stat(const std::string &stat);
  void clear_tracked_stats();

  void flush_caches();
  void pristine_machine();
  void set_cpu_clock_frequency(int MHz);

};



#endif
