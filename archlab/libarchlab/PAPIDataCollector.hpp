#ifndef PAPI_DATA_COLLECTOR_INCLUDED
#define PAPI_DATA_COLLECTOR_INCLUDED

#include"DataCollector.hpp"
#include <papi.h> 

class PAPIMeasurementInterval: public MeasurementInterval {
  std::vector<long long int> counts;
public:
  void start();
  void stop();
  json build_json();
};


class PAPIDataCollector: public DataCollector {
  friend PAPIMeasurementInterval;
  std::vector<int> events;
  
public:

  MeasurementInterval * newMeasurementInterval() {return new PAPIMeasurementInterval();}

  void track_event(int event) {events.push_back(event);}
  void clear_events() {events.clear();}

};
#endif
