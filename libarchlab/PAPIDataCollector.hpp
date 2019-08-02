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
  std::vector<int> rapl_events;
  int event_set;
  int rapl_event_set;
  
public:
  PAPIDataCollector();
  MeasurementInterval * newMeasurementInterval() {return new PAPIMeasurementInterval();}
  void get_usage(std::ostream &f);
  void track_stat(const std::string &stat);
  void clear_tracked_stats();

};
#endif
