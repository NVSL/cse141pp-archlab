#include <iostream>
#include <cpucounters.h>
#include "archlab.hpp"
#include <cstring>


// from https://github.com/nlohmann/json
#include <json.hpp>
#include <stdlib.h>
#include <sstream>      // std::stringstream
#include<time.h>
#include <stdarg.h>

#include "PCMDataCollector.hpp"
#include "PAPIDataCollector.hpp"
#include "PINDataCollector.hpp"
#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>


namespace po = boost::program_options;


DataCollector *theDataCollector = NULL;

extern "C" {
  int cpu_frequencies[] = { // Table of frequencies our servers support.
    3500,
    3100,
    2900,
    2700,
    2500,
    2300,
    2100,
    2000,
    1800,
    1600,
    1400,
    1200,
    1000,
    800,
    0
  };

  void archlab_parse_cmd_line(int *argc, char *argv[])
  {
    po::options_description desc("ArchLab driver");
    desc.add_options()
      ("help"      , "produce help message")
      ("stats-file", po::value<std::string>()->default_value(std::string("stats.csv")), "Stats output file")
      ("engine"    , po::value<std::string>()->default_value(std::string("native")), "Which data collector to use")
      ("stats"     , po::value<std::vector<std::string> >()->default_value(std::vector<std::string>(), "ARCHLAB_WALL_TIME"), "Which stats to collect");
    
    po::parsed_options parsed = po::command_line_parser(*argc, argv).options(desc).allow_unregistered().run();
  
    po::variables_map vm;
    po::store(parsed, vm);
    po::notify(vm);

    std::vector<std::string> to_pass_further = po::collect_unrecognized(parsed.options, po::include_positional);

    for (auto i: to_pass_further)
      std::cout << i << ' ';
  
    if (vm.count("help")) {
      std::cout << desc << "\n";
      exit(0);
    }
  
    if (boost::to_upper_copy<std::string>(vm["engine"].as<std::string>()) == "PAPI") {
      archlab_init(ARCHLAB_COLLECTOR_PAPI);
    } else if (boost::to_upper_copy<std::string>(vm["engine"].as<std::string>()) == "PIN") {
      archlab_init(ARCHLAB_COLLECTOR_PIN); 
    } else if (boost::to_upper_copy<std::string>(vm["engine"].as<std::string>()) == "NATIVE") {
      archlab_init(ARCHLAB_COLLECTOR_NONE); 
    } else if (boost::to_upper_copy<std::string>(vm["engine"].as<std::string>()) == "PCM") {
      archlab_init(ARCHLAB_COLLECTOR_PCM); 
    } else {
      std::cerr << "Unknown engine: " << vm["engine"].as<std::string>() << std::endl;
    }

    for(auto i: vm["stats"].as<std::vector<std::string > >() ) {
      theDataCollector->track_stat(i);
    }

    theDataCollector->set_stats_filename(vm["stats-file"].as<std::string>());


    *argc = to_pass_further.size() + 1;
    int c = 1;
    for(auto i: to_pass_further) {
      argv[c++] = strdup(i.c_str());
    }
    
  }

  void archlab_init(int collector)
  {
    if (collector == ARCHLAB_COLLECTOR_PCM) {
      theDataCollector = new PCMDataCollector();
    } else if (collector == ARCHLAB_COLLECTOR_PAPI) {
      theDataCollector = new PAPIDataCollector();
    } else if (collector == ARCHLAB_COLLECTOR_PIN) {
      theDataCollector = new PINDataCollector();
    } else if (collector == ARCHLAB_COLLECTOR_NONE) {
      theDataCollector = new DataCollector();
    } else {
      std::cerr << "Unknown data collector: " << collector << std::endl;
      exit(0);
    }
    theDataCollector->init();
  }

    
  void track_stat(char * stat)
  {
    theDataCollector->track_stat(std::string(stat));
  }
  
  void clear_tracked_stats()
  {
    theDataCollector->clear_tracked_stats();
  }

  void start_timing(const char * name...)
  {
    json kv;

    va_list args;
    va_start(args, name);

    while (char* k = va_arg(args, char *)) {
      //std::cerr << k << std::endl;
      char * v = va_arg(args, char *);
      //    std::cerr << v << std::endl;
      if (v == NULL) {
	std::cerr << "Missing value for last key-value pair in start_timing." << std::endl;
	exit(1);
      }
      kv[k] = v;
    }

    va_end(args);

    theDataCollector->start_timing(name, kv);
  }

  void stop_timing()  {theDataCollector->stop_timing();}

  void flush_caches() {
    theDataCollector->flush_caches();
  }
  

  void pristine_machine() {
    theDataCollector->pristine_machine();
  }

  void set_cpu_clock_frequency(int mhz)
  {
    theDataCollector->set_cpu_clock_frequency(mhz);
  }

  void archlab_write_stats() {
    theDataCollector->write_stats();
  }
  
}


