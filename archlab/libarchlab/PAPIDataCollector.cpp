#include"PAPIDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

using json = nlohmann::json;


PAPIDataCollector::PAPIDataCollector() : DataCollector("PAPI"){
  int retval = PAPI_library_init( PAPI_VER_CURRENT );
  if ( retval != PAPI_VER_CURRENT ) {
    std::cerr << "PAPI version mismatch." << std::endl;
  }
}

void PAPIDataCollector::track_stat(const std::string  & stat)
{
  int event;
  if (PAPI_OK == PAPI_event_name_to_code(stat.c_str(), &event)) {
    std::cerr << "Tracking " << stat << std::endl;
    events.push_back(event);
  } else {
    unknown_stat(stat);
  }
}

void PAPIDataCollector::get_usage(std::ostream &f) {
  f << "Run `papi_available` for a list available counters.  Also, not all combinations are allowed.  That's a likely source of failures." <<std::endl;
}
void PAPIDataCollector::clear_tracked_stats() {
  events.clear();
}

void PAPIMeasurementInterval::start()
{
  PAPIDataCollector* dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  int events[100];

  for (unsigned int i = 0; i < dc->events.size(); i++) {
    events[i] = dc->events[i];
  }
  int r = PAPI_start_counters(events, dc->events.size());

  if (r != PAPI_OK) {
    std::cerr<< "Failed to start measuring PAPI counters." << std::endl;
    exit(1);
  }
  _start->measure();
  
}

void PAPIMeasurementInterval::stop()
{
  PAPIDataCollector *dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  long long int values[100];
  _end->measure();
  int r = PAPI_stop_counters(values, dc->events.size());
  if (r != PAPI_OK) {
    std::cerr<< "Failed to read PAPI counters." << std::endl;
    exit(1);
  }

  counts.clear();
  for (unsigned int i = 0; i < dc->events.size(); i++) {
    counts.push_back(values[i]);
  }

}

json PAPIMeasurementInterval::build_json()
{
  PAPIDataCollector *dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  int l = dc->events.size();

  for (int i = 0; i < l; i++) {
    char b[PAPI_MAX_STR_LEN];
    PAPI_event_code_to_name(dc->events[i], b);
    kv[b] = counts[i];
  }
  
  MeasurementInterval::build_json();
  
  return kv; 
}


