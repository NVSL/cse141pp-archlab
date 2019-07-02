#include"PAPIDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

using json = nlohmann::json;


PAPIDataCollector::PAPIDataCollector() : DataCollector("PAPI"), event_set(PAPI_NULL){


    int retval = PAPI_library_init( PAPI_VER_CURRENT );
  if ( retval != PAPI_VER_CURRENT ) {
    std::cerr << "PAPI version mismatch." << std::endl;
  }

  if( PAPI_create_eventset(&event_set) != PAPI_OK )                         
    {                                                                      
      fprintf( stderr, "Problem creating EventSet\n" );                    
      exit(1);                                                             
    }                                                                      
  if( PAPI_assign_eventset_component( event_set, 0 ) != PAPI_OK )           
    {                                                                      
      fprintf( stderr, "Problem with PAPI_assign_eventset_component\n" );  
      exit(1);                                                             
    }                                                                      

  PAPI_option_t opt;
  memset( &opt, 0x0, sizeof( PAPI_option_t ) ); 
  opt.inherit.inherit = PAPI_INHERIT_ALL;
  opt.inherit.eventset = event_set;
  if( ( retval = PAPI_set_opt( PAPI_INHERIT, &opt ) ) != PAPI_OK ) {                                                                      
    fprintf( stderr, "Problem with PAPI_set_opt\n" );                    
    exit(1);                                                             
  }
  
}

void PAPIDataCollector::track_stat(const std::string  & stat)
{
  int event;
  if (PAPI_OK == PAPI_event_name_to_code(stat.c_str(), &event)) {
    std::cerr << "Tracking " << stat << std::endl;
    events.push_back(event);
    if( PAPI_add_event(event_set, event) != PAPI_OK ) {                                                                      
      std::cerr << "Problem adding " << stat << "\n";
      exit(1);                                                             
    }                                                                      
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
  /*  int events[100];

  for (unsigned int i = 0; i < dc->events.size(); i++) {
    events[i] = dc->events[i];
    }*/
  int r = PAPI_start(dc->event_set);
    
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
  int r = PAPI_stop(dc->event_set, values);
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


