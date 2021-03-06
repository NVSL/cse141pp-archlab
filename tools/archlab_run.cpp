#include "archlab.hpp"
#include <stdlib.h>
#include <getopt.h>
#include <iostream>
#include<string.h>
#include<unistd.h>
#include <boost/program_options.hpp>
namespace po = boost::program_options;


int main(int argc, char *argv[]) {



  int i = 0;
  while (i != argc && std::string(argv[i]) != "--") i++;
  if (i == argc || i == argc - 1) {
    std::cerr << "Missing command. Usage: archlab_run <options> -- <command>\n";
    exit(1);
  }

  int command_args = (argc - (i + 1));
  argc = i;
  i++; // eat the '--'
  
  char *commandv[command_args + 1];
  for(int k = 0; k < command_args; k++) {
    commandv[k] = argv[i+k];
    //std::cerr << commandv[0] << "|";
  }
  commandv[command_args] = NULL;

  //archlab_add_option<float>("stats-period", stats_period, 1, "How frequently to collect statistics");
  
  archlab_parse_cmd_line(&argc, argv);
  
  {
    ArchLabTimer timer; // create it.
    pristine_machine(); // reset the machine
    timer.
      go(); // Start measuring

    for(int i = 0;i  < 10000;i++) {}
    theDataCollector->run_child(commandv[0], commandv); 
  }

  archlab_write_stats();
  
  return 0;
}


