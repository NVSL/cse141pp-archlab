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


po::options_description archlab_cmd_line_options("ArchLab driver");
std::vector<BaseOptionSpec*> options;

po::variables_map archlab_parsed_options;
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
    archlab_cmd_line_options.add_options()
      ("help"      , "produce help message")
      ("stats-file", po::value<std::string>()->default_value(std::string("stats.csv")), "Stats output file")
      ("engine"    , po::value<std::string>()->default_value(std::string("native")), "Which data collector to use")
      ("stat"      , po::value<std::vector<std::string> >()->default_value(std::vector<std::string>(), "ARCHLAB_WALL_TIME"), "Which stats to collect");
    
    po::parsed_options parsed = po::command_line_parser(*argc, argv).options(archlab_cmd_line_options).allow_unregistered().run();
    po::store(parsed, archlab_parsed_options);
    po::notify(archlab_parsed_options);

    for(auto i: options) {
      i->assign(archlab_parsed_options);
    }

    std::vector<std::string> to_pass_further = po::collect_unrecognized(parsed.options, po::include_positional);

    if (boost::to_upper_copy<std::string>(archlab_parsed_options["engine"].as<std::string>()) == "PAPI") {
      archlab_init(ARCHLAB_COLLECTOR_PAPI);
    } else if (boost::to_upper_copy<std::string>(archlab_parsed_options["engine"].as<std::string>()) == "PIN") {
      archlab_init(ARCHLAB_COLLECTOR_PIN); 
    } else if (boost::to_upper_copy<std::string>(archlab_parsed_options["engine"].as<std::string>()) == "NATIVE") {
      archlab_init(ARCHLAB_COLLECTOR_NONE); 
    } else if (boost::to_upper_copy<std::string>(archlab_parsed_options["engine"].as<std::string>()) == "PCM") {
      archlab_init(ARCHLAB_COLLECTOR_PCM); 
    } else {
      std::cerr << "Unknown engine: '" << archlab_parsed_options["engine"].as<std::string>() << "'.   Options are: papi, pin, native, pcm." << std::endl;
      abort();
    }
    std::cerr << "Loading " << theDataCollector->get_name() << " engine." << std::endl;
    
    if (archlab_parsed_options.count("help")) {
      std::cout << archlab_cmd_line_options << std::endl;
      
      if (theDataCollector) {
	theDataCollector->get_usage(std::cerr);
      }
    }
  
    for(auto i: archlab_parsed_options["stat"].as<std::vector<std::string > >() ) {
      theDataCollector->track_stat(i);
    }

    theDataCollector->set_stats_filename(archlab_parsed_options["stats-file"].as<std::string>());


    *argc = to_pass_further.size() + 1;
    int c = 1;
    for(auto i: to_pass_further) {
      argv[c++] = strdup(i.c_str());
    }
    if (archlab_parsed_options.count("help")) {
      argv[c++] = strdup("--help");
      (*argc)++;
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

    const char * k = name;
    const char * v = NULL;
    while (k && (v = va_arg(args, char *))) {
      //    std::cerr << v << std::endl;
      if (v == NULL) {
	std::cerr << "Missing value for last key-value pair in start_timing." << std::endl;
	exit(1);
      }
      kv[k] = v;
      k = va_arg(args, char *);
    }
    va_end(args);

    theDataCollector->start_timing(kv);
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

  uint64_t si_parse(const char *s)
  {
    static std::map<std::string, uint64_t> prefixes;
    if (!prefixes.size()) {
      prefixes["ki"] = 1024;
      prefixes["Mi"] = 1024*1024;
      prefixes["Gi"] = 1024*1024*1024;
      prefixes["Ti"] = 1024ull*1024*1024*1024;
      prefixes["k"] = 1000;
      prefixes["M"] = 1000*1000;
      prefixes["G"] = 1000*1000*1000;
      prefixes["T"] = 1000ull*1000*1000*1000;
    }

    char *tail;
    uint64_t b = strtoll(s, &tail, 0);

    auto p = prefixes.find(tail);
    if (*tail == '\0') {
      return b;
    } else if (p != prefixes.end()) {
      return b * p->second;
    } else {
      std::cerr << "unknown suffix: " << tail << std::endl;
      abort();
    }
    
  }

}


void ArchLabTimer::go() {
  theDataCollector->start_timing(kv);
  timing = true;
}

void ArchLabTimer::go(std::function<void()> f)
{
  timing = true;
  theDataCollector->start_timing(kv);
  f();
  theDataCollector->stop_timing();
  timing = false;
}

ArchLabTimer::~ArchLabTimer() {
  if (timing) {
    theDataCollector->stop_timing();
  }
}


void archlab_add_flag(const std::string & name, bool & dest, const bool& def, const std::string & desc) {
  archlab_cmd_line_options.add_options()
    (name.c_str(), desc.c_str());
  options.push_back(new FlagOptionSpec(name, dest));
}
