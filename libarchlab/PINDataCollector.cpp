#include"PINDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>


using json = nlohmann::json;


extern "C" {
  ArchLabPinTool * pin_get_tool() __attribute__((noinline));
#define UNPATCHED_PIN_FUNC  std::cerr << "Tried to invoke " << __FUNCTION__ << " on pin tool, but function is not patched." << std::endl
  ArchLabPinTool * pin_get_tool() 
  {
    UNPATCHED_PIN_FUNC;
    return new DummyPinTool();
  }
}

void PINDataCollector::init() {
  tool = pin_get_tool();
  DataCollector::init();
}

void PINDataCollector::get_usage(std::ostream &f)
{
  char *names[PIN_MAX_REGISTERS];
  int count = 0;
  tool->get_available_registers(&count, names);
  f << "Available registers " << std::endl;
  for(int i= 0; i < count; i++){ 
    f << "  " << names[i] << std::endl;
  }
}

void PINDataCollector::track_stat(const std::string  & stat)
{
  int r = tool->get_register_by_name(stat.c_str());
  if (r == -1) {
    unknown_stat(stat);
    get_usage(std::cerr);
    abort();
  } else {
    tracked_registers.push_back(r);
  }
}

void PINDataCollector::clear_tracked_stats() {
  tracked_registers.clear();
}


void PINMeasurementInterval::start()
{
  _start->measure();
  collector->tool->start_collection(NULL);
}

void PINMeasurementInterval::stop()
{
  _end->measure();
  collector->tool->stop_collection(registers);
}

json PINMeasurementInterval::build_json()
{
  for(auto i: dynamic_cast<PINDataCollector*>(collector)->tracked_registers) {
    kv[collector->tool->get_register_by_index(i)] = registers[i];
  }
  
  MeasurementInterval::build_json();

  return kv; 
}


void PINDataCollector::flush_caches() {
}

void PINDataCollector::pristine_machine()
{
  tool->reset();
}

void PINDataCollector::set_cpu_clock_frequency(int MHz) {
  std::cerr << "CPU Frequency is irrelevant with PIN" << std::endl;
}

