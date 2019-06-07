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

  MeasurementInterval * newMeasurementInterval() {return new PINMeasurementInterval();}

  void track_event(int index) {
    tracked_registers.push_back(index);
  }

};


extern "C" {
void pin_start_collection(uint64_t * data);
void pin_stop_collection(uint64_t * data);
}

#endif
