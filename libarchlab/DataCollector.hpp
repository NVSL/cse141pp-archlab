#ifndef DATA_COLLECTOR_INCLUDED
#define DATA_COLLECTOR_INCLUDED
#include<stdint.h>
#include"archlab.hpp"
#include <json.hpp>
using json = nlohmann::json;
  
class Measurement {
public:
	double time;
	int MHz;
	virtual void measure() ;
	virtual ~Measurement() {}
};

class DataCollector;

class MeasurementInterval {
protected:
	json kv;
	Measurement * _start;
	Measurement * _end;
	friend DataCollector;
	explicit MeasurementInterval(Measurement*s, Measurement *e): _start(s), _end(e) {} 
public:
	MeasurementInterval(): _start(new Measurement), _end(new Measurement) {}
  
	virtual ~MeasurementInterval() {
		delete _start;
		delete _end;
	}
  
	template<class T>
	void add_field(const char * name, const T & v) {
		kv[name] = v;
	}
  
	void add_string(char * name, char * value);
	void add_double(char * name, double value);
	template <class T>
	T get_value(const std::string & k) {return kv[k].get<T>();}
	json& get_kv() {return kv;}
	virtual void start();
	virtual void stop();
	virtual json build_json();
};


class DataCollector {
	friend MeasurementInterval;
	friend Measurement;
	std::vector<MeasurementInterval* > stored_intervals;
	std::string stats_filename;
	const std::string collector_name;
	MeasurementInterval * current_interval;
	bool timing_something;
	json default_kv;
	std::map<pthread_t*, pthread_t*> threads;
	std::map<std::string, std::string> output_aliases;

	std::vector<std::string> my_stats;
	
	std::vector<std::string> tags;
	std::vector<std::string> stats;
	std::vector<std::string> calcs;
	int current_nominal_mhz;
	
protected:
	virtual MeasurementInterval * newMeasurementInterval() {return new MeasurementInterval();}
	explicit DataCollector(const std::string &name): collector_name(name), current_interval(NULL), timing_something(false), current_nominal_mhz(1000)  {}
public:

	typedef pthread_t *Thread;
  
	// https://software.intel.com/en-us/articles/disclosure-of-hw-prefetcher-control-on-some-intel-processors
	enum {PREFETCH_L2 = 1,
	      PREFETCH_L2_PAIR = 2,
	      PREFETCH_L1_NEXT_LINE = 4,
	      PREFETCH_L1_SEQ_HIST = 8};

	DataCollector() : DataCollector("Native"){}
  
  
	virtual void init();
	virtual void start_timing(json & kv);
	virtual void stop_timing();
	virtual void pristine_machine();
	virtual void enable_prefetcher(int flags = 15);  // flags should be some |'d combination of the PREFETCH_* enums above.
	virtual void disable_prefetcher();
	virtual void flush_caches();
	virtual void set_cpu_clock_frequency(int MHz);

	virtual void track_stat(const std::string &stat);
	virtual void clear_tracked_stats();
	virtual void get_usage(std::ostream & f);
	virtual int  run_child(char *exec, char *argv[]);
	
	void set_stat_output_name(const std::string & original_name, const std::string & output_name);
	Thread run_thread(void *(*start_routine) (void *), void *arg);
	virtual void bind_this_thread_to_core(int c);
  
	void set_stats_filename(const std::string &s) {stats_filename = s;}
	void enqueue_interval(MeasurementInterval *mi) {
		stored_intervals.push_back(mi);
		current_interval = mi;
		timing_something = true;
	}

	std::string build_csv_row(MeasurementInterval * mi);
	std::string build_csv_header(MeasurementInterval * mi);

	std::string rename_stat(const std::string & s);
	json build_json();
	void write_json(const char * filename);
	void write_json(std::ostream & out);
	void write_csv(const char * filename);
	void write_csv(std::ostream & out);
	void write_stats();
	template<class T>
	void set_tag(const std::string & tag, const T & value) {
		current_interval->add_field(tag.c_str(), value);
	}
	void register_stat(const std::string & stat);
	void register_calc(const std::string & exp);
	template<class T>
	void register_tag(const std::string & key, const T & value, bool one_off=false) {
		if (!one_off) 
			add_default_kv(key,value);
		
		for(auto t: tags) {
			if (t == key) return;
		}
		tags.push_back(key);
	}


	std::vector<MeasurementInterval* > * get_intervals() {
		return & stored_intervals;
	}
private:
	std::vector<std::string> get_ordered_column_names();
	template<class T>
	void add_default_kv(const std::string & key, const T & value) {
		default_kv[key] = value;
	}
	
public:
	const std::string & get_name() const {return collector_name;} 
	void unknown_stat(const std::string & s);
};

#endif
