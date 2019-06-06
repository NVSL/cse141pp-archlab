#ifndef PCM_DATA_COLLECTOR_INCLUDED
#define PCM_DATA_COLLECTOR_INCLUDED

#include"DataCollector.hpp"
#include <cpucounters.h>


class PCMMeasurementInterval;
class PCMMeasurement: public Measurement {
  friend PCMMeasurementInterval;
  SystemCounterState pcm_system_counter_state;
  std::vector<SocketCounterState> pcm_socket_counter_state;
  std::vector<CoreCounterState> pcm_core_counter_state;
public:
  void measure();
};

class PCMMeasurementInterval: public MeasurementInterval {
public:
  PCMMeasurementInterval(): MeasurementInterval(new PCMMeasurement,new PCMMeasurement) {}
  json build_json();
};


class PCMDataCollector: public DataCollector {
public:
  void init();

  MeasurementInterval * newMeasurementInterval() {return new PCMMeasurementInterval();}

  
};
#endif
