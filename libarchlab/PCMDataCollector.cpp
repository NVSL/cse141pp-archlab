#include"PCMDataCollector.hpp"
#include <iostream>
#include <cstring>
#include <stdlib.h>
#include <json.hpp>
using json = nlohmann::json;

#define NAME_KEY "Name"

void PCMDataCollector::init()
{
  PCM::getInstance()->program();
  DataCollector::init();
}

#define PCM_MEASUREMENT_STAT_FIELDS \
  MEASUREMENT_STAT_FIELD(IPC, core)			\
  MEASUREMENT_STAT_FIELD(L3CacheHitRatio, core)		\
  MEASUREMENT_STAT_FIELD(L3CacheMisses, core)		\
  MEASUREMENT_STAT_FIELD(L3CacheHits, core)			\
  MEASUREMENT_STAT_FIELD(L2CacheHitRatio, core)			\
  MEASUREMENT_STAT_FIELD(L2CacheHits, core)				\
  MEASUREMENT_STAT_FIELD(L2CacheMisses, core)				\
  MEASUREMENT_STAT_FIELD(AverageFrequency, core) \
  MEASUREMENT_STAT_FIELD(BytesReadFromMC, socket) \
  MEASUREMENT_STAT_FIELD(BytesWrittenToMC, socket) \
  MEASUREMENT_STAT_FIELD(ConsumedEnergy, socket)		   \
  MEASUREMENT_STAT_FIELD(DRAMConsumedEnergy, socket)		   
  //  MEASUREMENT_STAT_FIELD(BytesReadFromMC)

#define CUSTOM_MEASUREMENT_STAT_FIELDS \
  MEASUREMENT_STAT_FIELD(WallTime, core)

#define MEASUREMENT_STAT_FIELDS \
  CUSTOM_MEASUREMENT_STAT_FIELDS\
  PCM_MEASUREMENT_STAT_FIELDS

#define SYSTEM_STAT_FIELDS \
  SYSTEM_STAT_FIELD(NumCores)\
  SYSTEM_STAT_FIELD(NumSockets)\
  SYSTEM_STAT_FIELD(SMT)\
  SYSTEM_STAT_FIELD(NominalFrequency)\
  SYSTEM_STAT_FIELD(CPUModel)\
  SYSTEM_STAT_FIELD(MaxIPC)
//  SYSTEM_STAT_FIELD(OriginalCPUModel)		

#define ALL_FIELDS \
  CUSTOM_MEASUREMENT_STAT_FIELDS\
  SYSTEM_STAT_FIELDS\
  PCM_MEASUREMENT_STAT_FIELDS

json PCMMeasurementInterval::build_json()
{
  PCMMeasurement * start = dynamic_cast<PCMMeasurement*>(_start);
  PCMMeasurement * end = dynamic_cast<PCMMeasurement*>(_end);
  
#define MEASUREMENT_STAT_FIELD(s, where) kv[#s] = get##s(start->pcm_##where##_counter_state[0], end->pcm_##where##_counter_state[0]);
PCM_MEASUREMENT_STAT_FIELDS
#undef MEASUREMENT_STAT_FIELD

#define SYSTEM_STAT_FIELD(s) kv[#s] = PCM::getInstance()->get##s();
  SYSTEM_STAT_FIELDS;
#undef SYSTEM_STAT_FIELD
 
 kv["ConsumedEnergy"] = kv["ConsumedEnergy"].get<double>() * PCM::getInstance()->getJoulesPerEnergyUnit();
 kv["DRAMConsumedEnergy"] = kv["DRAMConsumedEnergy"].get<double>() * PCM::getInstance()->getJoulesPerEnergyUnit();

 MeasurementInterval::build_json();
  
 return kv; 
}


void PCMMeasurement::measure() 
{
  Measurement::measure();
  PCM::getInstance()->getAllCounterStates(pcm_system_counter_state,
					  pcm_socket_counter_state,
					  pcm_core_counter_state);
}

