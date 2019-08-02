#include"PAPIDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>

using json = nlohmann::json;

int num_events = 0;

int find_rapl_component_num() {
  int numcmp = PAPI_num_components();
  int cid;
  const PAPI_component_info_t *cmpinfo = NULL;  
  for(cid=0; cid<numcmp; cid++) {

    if ( (cmpinfo = PAPI_get_component_info(cid)) == NULL) {
      fprintf(stderr,"PAPI_get_component_info failed\n");
      exit(1);
    }
    
    if (strstr(cmpinfo->name,"rapl")) {
      //printf("Found rapl component at cid %d\n", cid);
      
      if (cmpinfo->disabled) {
	fprintf(stderr,"No rapl events found: %s\n",
		cmpinfo->disabled_reason);
	exit(1);
      }
      break;
    }
  }

  /* Component not found */
  if (cid==numcmp) {
    fprintf(stderr,"No rapl component found\n");
    exit(1);
  }
  return cid;
  
}  
void dump_rapl() 
{

#define MAX_EVENTS 128

  char events[MAX_EVENTS][BUFSIZ];
  
  int retval,cid;
  int EventSet = PAPI_NULL;
  int i,code,enum_retval;
  PAPI_event_info_t evinfo;

  char event_name[BUFSIZ];

  cid = find_rapl_component_num();
  /* Find Events */
  code = PAPI_NATIVE_MASK;

  enum_retval = PAPI_enum_cmp_event( &code, PAPI_ENUM_FIRST, cid );

  while ( enum_retval == PAPI_OK ) {

    retval = PAPI_event_code_to_name( code, event_name );
    if ( retval != PAPI_OK ) {
      printf("Error translating %#x\n",code);
      exit(1);
    }

    printf("Found: %s\n",event_name);
    printf("Found: %s\n",event_name);
    strncpy(events[num_events],event_name,BUFSIZ);
    num_events++;
    
    /* Find additional event information: unit, data type */
    retval = PAPI_get_event_info(code, &evinfo);
    if (retval != PAPI_OK) {
      printf("Error getting event info for %#x\n",code);
      exit(1);
    }

    enum_retval = PAPI_enum_cmp_event( &code, PAPI_ENUM_EVENTS, cid );

  }

  if (num_events==0) {
    printf("Error!  No RAPL events found!\n");
    exit(1);
  }

  /* Create EventSet */
  retval = PAPI_create_eventset( &EventSet );
  if (retval != PAPI_OK) {
    fprintf(stderr,"Error creating eventset!\n");
  }
  
  for(i=0;i<num_events;i++) {

    fprintf(stderr, "added %s\n", events[i]);
    retval = PAPI_add_named_event( EventSet, events[i] );
    if (retval != PAPI_OK) {
      fprintf(stderr,"Error adding event %s\n",events[i]);
    }
  }
}

PAPIDataCollector::PAPIDataCollector() : DataCollector("PAPI"), event_set(PAPI_NULL), rapl_event_set(PAPI_NULL) {


    int retval = PAPI_library_init( PAPI_VER_CURRENT );
    if ( retval != PAPI_VER_CURRENT ) {
      std::cerr << "PAPI version mismatch." << std::endl;
    }

    //dump_rapl();
    if( (retval = PAPI_create_eventset(&event_set)) != PAPI_OK )
      {                                                                      
	fprintf( stderr, "Problem creating EventSet: %s\n", PAPI_strerror(retval));        
	exit(1);                                                             
      }

    if( (retval = PAPI_create_eventset(&rapl_event_set)) != PAPI_OK )                         
      {                                                                      
	fprintf( stderr, "Problem creating rapl EventSet: %s\n", PAPI_strerror(retval));        
	exit(1);                                                             
      }
    
    if( (retval = PAPI_assign_eventset_component( event_set, 0)) != PAPI_OK )           
      {                                                                      
	fprintf( stderr, "Problem with PAPI_assign_eventset_component: %s\n", PAPI_strerror(retval));
	exit(1);                                                             
      }
    
    if( PAPI_assign_eventset_component( rapl_event_set, find_rapl_component_num() ) != PAPI_OK )           
      {                                                                      
	fprintf( stderr, "Problem with PAPI_assign_eventset_component for rapl\n" );  
	exit(1);                                                             
      }
    
    PAPI_option_t opt;
    memset( &opt, 0x0, sizeof( PAPI_option_t ) ); 
    opt.inherit.inherit = PAPI_INHERIT_ALL;
    opt.inherit.eventset = event_set;
    if( ( retval = PAPI_set_opt( PAPI_INHERIT, &opt ) ) != PAPI_OK ) {                                                                      
      fprintf( stderr, "Problem with PAPI_set_opt: %s\n", PAPI_strerror(retval) );                    
      exit(1);                                                             
    }
}

void PAPIDataCollector::track_stat(const std::string  & stat)
{
  int event;
  int r;
  if (PAPI_OK == PAPI_event_name_to_code(stat.c_str(), &event)) {
    std::cerr << "Tracking " << stat << std::endl;

    if( (r = PAPI_add_named_event(event_set, stat.c_str())) != PAPI_OK ) {
      if( (r = PAPI_add_named_event(rapl_event_set, stat.c_str())) != PAPI_OK ) {
	std::cerr << "Problem adding " << stat << ": " << PAPI_strerror(r) << "\n";
	exit(1);                                                             
      } else {
	rapl_events.push_back(event);
      }
    } else {
      events.push_back(event);
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
  rapl_events.clear();
}

void PAPIMeasurementInterval::start()
{
  PAPIDataCollector* dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);

  if (dc->events.size()) {
    int r = PAPI_start(dc->event_set);
    if (r != PAPI_OK) {
      std::cerr<< "Failed to start measuring PAPI counters: " << PAPI_strerror(r) << std::endl;
      exit(1);
    }
  }
  
  if (dc->rapl_events.size()) {
    int r = PAPI_start(dc->rapl_event_set);
    if (r != PAPI_OK) {
      std::cerr<< "Failed to start measuring rapl PAPI counters: " << PAPI_strerror(r) << std::endl;
      exit(1);
    }
  }
  
  _start->measure();
  
}

void PAPIMeasurementInterval::stop()
{
  PAPIDataCollector *dc = dynamic_cast<PAPIDataCollector*>(theDataCollector);
  long long int values[100];
  _end->measure();

  counts.clear();

  if (dc->events.size()) { 
    int r = PAPI_stop(dc->event_set, values);
    if (r != PAPI_OK) {
      std::cerr<< "Failed to read PAPI counters: " << PAPI_strerror(r) << std::endl;
      exit(1);
    }
    
    for (unsigned int i = 0; i < dc->events.size(); i++) {
      counts.push_back(values[i]);
    }
  }
  
  if (dc->rapl_events.size()) { 
    int r = PAPI_stop(dc->rapl_event_set, values);
    if (r != PAPI_OK) {
      std::cerr<< "Failed to read rapl PAPI counters: " << PAPI_strerror(r) << std::endl;
      exit(1);
    }
    
    for (unsigned int i = 0; i < dc->rapl_events.size(); i++) {
      counts.push_back(values[i]);
    }
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

  int l2 = dc->rapl_events.size();

  for (int i = 0; i < l2; i++) {
    char b[PAPI_MAX_STR_LEN];
    PAPI_event_code_to_name(dc->rapl_events[i], b);
    kv[b] = counts[i + l];
  }
  
  MeasurementInterval::build_json();
  
  return kv; 
}


