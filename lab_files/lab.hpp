#ifndef LAB_INCLUDED
#define LAB_INCLUDED

#include<iostream>
#include <cpucounters.h>

void write_system_config(const char * filename);
void write_system_config(std::ostream & out);
void write_run_stats(const char * filename,
		     const SystemCounterState & before,
		     const SystemCounterState & after);
void write_run_stats(std::ostream & out,
		     const SystemCounterState & before,
		     const SystemCounterState & after);

#endif
