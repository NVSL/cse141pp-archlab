#include <iostream>
#include <cpucounters.h>
#include "lab.hpp"

// from https://github.com/nlohmann/json
#include <json.hpp>

// for convenience
using json = nlohmann::json;

void write_system_config(const char * filename)
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate()) 
    std::cerr << "Opening " << filename << " failed." << std::endl;
  write_system_config(out);
  out.close();
}

void write_system_config(std::ostream & out)
{
#define GET_SYS_STAT(j, s) j[#s] = PCM::getInstance()->get##s()
  json system;
  GET_SYS_STAT(system, NumCores);
  GET_SYS_STAT(system, NumSockets);
  GET_SYS_STAT(system, SMT);
  GET_SYS_STAT(system, NominalFrequency);
  GET_SYS_STAT(system, CPUModel);
  GET_SYS_STAT(system, OriginalCPUModel);
  GET_SYS_STAT(system, MaxIPC);
  out << system.dump(4) << std::endl;  
}

void write_run_stats(const char * filename,
		     const SystemCounterState & before,
		     const SystemCounterState & after)
  
{
  std::fstream out;
  out.open(filename, std::ios_base::out);
  if (out.rdstate()) 
    std::cerr << "Opening " << filename << " failed." << std::endl;

  write_run_stats(out, before, after);
  out.close();
}


void write_run_stats(std::ostream & out,
		     const SystemCounterState & before,
		     const SystemCounterState & after)
{

#define GET_RUN_STAT(j, s, before, after) j[#s] = get##s(before, after)

  json j;
  GET_RUN_STAT(j, IPC, before, after);
  GET_RUN_STAT(j, L3CacheHitRatio, before, after);
  GET_RUN_STAT(j, BytesReadFromMC, before, after);
  out << j.dump(4) << std::endl;  
}

