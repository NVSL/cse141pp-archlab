#ifndef PIN_DATA_COLLECTOR_INCLUDED
#define PIN_DATA_COLLECTOR_INCLUDED

#include"DataCollector.hpp"
#include"pin-tools/ArchLabPinTool.hpp"


extern char * archlab_pin_registers[];

class PINDataCollector;
class PINMeasurementInterval: public MeasurementInterval {
  uint64_t registers[PIN_MAX_REGISTERS];
  PINDataCollector * collector;
public:
  PINMeasurementInterval(PINDataCollector *dc) : collector(dc) {}
  void start();
  void stop();
  json build_json();
};

class PINDataCollector: public DataCollector {
  friend PINMeasurementInterval;

  ArchLabPinTool * tool;
  std::vector<int> tracked_registers;
public:

  PINDataCollector() : DataCollector("PIN"), tool(NULL){}
  MeasurementInterval * newMeasurementInterval() {return new PINMeasurementInterval(this);}

  void init();
  void get_usage(std::ostream &f);
  void track_stat(const std::string &stat);
  void clear_tracked_stats();

  void flush_caches();
  void pristine_machine();
  void set_cpu_clock_frequency(int MHz);

};



#endif
