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
  PAPIDataCollector() : DataCollector("PAPI"){}
  MeasurementInterval * newMeasurementInterval() {return new PAPIMeasurementInterval();}

  void track_stat(const std::string &stat);
  void clear_tracked_stats();
};
#endif
