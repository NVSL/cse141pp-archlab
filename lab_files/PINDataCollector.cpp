#include"PINDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

using json = nlohmann::json;

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
    kv[archlab_pin_registers[*i]] = registers[*i];
  }
  
  MeasurementInterval::build_json();

  return kv; 
}

void pin_start_collection(uint64_t * data){
  std::cerr << "Tried to start PIN data collection, but function is not patched." << std::endl;
}
void pin_stop_collection(uint64_t * data)
{
  std::cerr << "Tried to stop PIN data collection, but function is not patched." << std::endl;
}
