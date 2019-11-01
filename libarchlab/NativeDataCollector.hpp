#ifndef NATIVE_DATA_COLLECTOR_INCLUDED
#define NATIVE_DATA_COLLECTOR_INCLUDED

#include"DataCollector.hpp"
#include <cpucounters.h>

class NativeDataCollector: public DataCollector {
public:
	NativeDataCollector() : DataCollector("Native"){}

	void pristine_machine() {}
	void enable_prefetcher(int flags = 15) {}
	void disable_prefetcher() {}
	void flush_caches() {}
	void set_cpu_clock_frequency(int MHz) {}
};
#endif
