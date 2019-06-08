#include"PINDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

#include "pin-tools/archlab_pintool.hpp"

using json = nlohmann::json;


extern "C" {

#define UNPATCHED_PIN_FUNC     std::cerr << "Tried to invoke " << __FUNCTION__ << " on pin tool, but function is not patched." << std::endl
  void pin_start_collection(uint64_t * data){
    UNPATCHED_PIN_FUNC;
  }
  void pin_stop_collection(uint64_t * data)
  {
    UNPATCHED_PIN_FUNC;
  }
  
  void pin_reset_tool()
  {
    UNPATCHED_PIN_FUNC;
  }
  
  int pin_get_register_by_name(const char *)
  {
    UNPATCHED_PIN_FUNC;
    return -1;
  }
  const char * pin_get_register_by_index(int i)
  {
    UNPATCHED_PIN_FUNC;
    return NULL;
  }
}


void PINDataCollector::track_stat(const std::string  & stat)
{
  int r = pin_get_register_by_name(stat.c_str());
  if (r == -1) {
    unknown_stat(stat);
  }
}

void PINDataCollector::clear_tracked_stats() {
  tracked_registers.clear();
}


void PINMeasurementInterval::start()
{
  //PINDataCollector* dc = dynamic_cast<PINDataCollector*>(theDataCollector);
  _start->measure();
  pin_start_collection(NULL);
}

void PINMeasurementInterval::stop()
{
  //PINDataCollector *dc = dynamic_cast<PINDataCollector*>(theDataCollector);
  _end->measure();
  pin_stop_collection(registers);
}

json PINMeasurementInterval::build_json()
{
  PINDataCollector *dc = dynamic_cast<PINDataCollector*>(theDataCollector);

  
  for(auto i = dc->tracked_registers.begin();
      i != dc->tracked_registers.end();
      i++) {
    kv[pin_get_register_by_index(*i)] = registers[*i];
  }
  
  MeasurementInterval::build_json();

  return kv; 
}


void PINDataCollector::flush_caches() {
}

void PINDataCollector::pristine_machine()
{
  pin_reset_tool();
}

void PINDataCollector::set_cpu_clock_frequency(int MHz) {
  std::cerr << "CPU Frequency is irrelevant with PIN" << std::endl;
}

