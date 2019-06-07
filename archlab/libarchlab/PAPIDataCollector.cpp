#include"PAPIDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

using json = nlohmann::json;

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


