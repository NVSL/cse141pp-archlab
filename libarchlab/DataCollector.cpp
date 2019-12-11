#include "archlab.h"
#include "DataCollector.hpp"
#include <iostream>
#include <cstring>
#include <json.hpp>
#include <stdlib.h>
#include <sstream>      // std::stringstream
#include <time.h>
#include <fcntl.h>
#include <stdarg.h>
#include <sys/types.h>
#include <unistd.h>
#include <fstream>
#include<pthread.h>

#include <sys/stat.h>
#include <cache_control/cache_control.h>
#include <sys/ioctl.h>
#include <sched.h>
#include <sys/wait.h> 
#include <sys/sysinfo.h>



// for convenience
using json = nlohmann::json;


void DataCollector::init() 
{
	srand(time(0));
}

void DataCollector::bind_this_thread_to_core(int c)
{
	cpu_set_t my_set;        /* Define your cpu_set bit mask. */
	CPU_ZERO(&my_set);       /* Initialize it all to 0, i.e. no CPUs selected. */
	CPU_SET(c, &my_set);     /* set the bit that represents core 7. */
	sched_setaffinity(0, sizeof(cpu_set_t), &my_set); /* Set affinity of tihs process to the defined mask, i.e. only 7. */
}

DataCollector::Thread run_thread(void *(*start_routine) (void *), void *arg)
{
	pthread_t * n = new pthread_t;
	int r = pthread_create(n, NULL, start_routine, arg);
	if (r != 0) {
		std::cerr<< "Couldn't Start thread: " << strerror(errno) <<"\n";
		exit(1);
	}
	//threads[n] = n;
	return n;
}



int DataCollector::run_child(char *exec, char *argv[])
{
	pid_t child_pid;
	if( (child_pid = fork()) == 0 )  //Purposeful assignment, not comparison
	{
		int r = execvp(exec, argv);
		std::cerr << "Exec returned\n";
		if (r == -1) {
			std::cerr << "Couldn't exec '" << exec << "': " << strerror(errno) << "\n";
			exit(1);
		}
	}
	else if( child_pid < 0 )
	{
		fprintf( stderr, "Failed to create child process. Exiting...\n" );
		exit(1);
	}
  
	int status;
	//usleep( (useconds_t) 5000 ); Not sure why leo had this in here.
	pid_t r = waitpid(child_pid, &status,0);
	if (r == -1) {
		std::cerr << "Couldn't wait for child to exit. I'm exiting...\n";
		exit(1);
	}

	return WEXITSTATUS(status);
}

void DataCollector::get_usage(std::ostream & f) {
}

void DataCollector::track_stat(const std::string  & stat)
{
	if (stat == "ARCHLAB_WALL_TIME" ||
	    stat == "ARCHLAB_CLOCK_SPEED_MHZ") {
		theDataCollector->my_stats.push_back(stat);
	} else {
		unknown_stat(stat);
	}
}


void DataCollector::clear_tracked_stats() {
}

void DataCollector::register_calc(const std::string & exp) {
	add_default_kv(exp,"");
	calcs.push_back(exp);
}

void DataCollector::register_stat(const std::string & stat) {
	stats.push_back(stat);
}


void DataCollector::start_timing(json & kv)
{
	MeasurementInterval *n = newMeasurementInterval();
	n->kv = default_kv;
	if (!kv.is_null())
		n->kv.merge_patch(kv);
	//std::cerr << default_kv.dump() << " c\n";
	//std::cerr << kv.dump() << " a\n";
	//std::cerr << n->kv.dump() << " b\n";
	for(auto & k: kv.items()) {
		register_tag(k.key(), "", true);
	}
	
	if (current_interval) {
		std::cerr << "You are already timing something.  You can't time something else." << std::endl;
		exit(1);
	}
	enqueue_interval(n);
	current_interval = n;
	n->start();
}

void DataCollector::stop_timing()
{

	if (!current_interval) {
		std::cerr << "You are not currently timing anything." << std::endl;
		exit(1);
	}
  
	current_interval->stop();
	current_interval = NULL;
}

json MeasurementInterval::build_json()
{
	for(auto &s: theDataCollector->my_stats) {
		if (s == "ARCHLAB_WALL_TIME") 
			kv["ARCHLAB_WALL_TIME"] = _end->time - _start->time;
		else if (s == "ARCHLAB_CLOCK_SPEED_MHZ")
			kv["ARCHLAB_CLOCK_SPEED_MHZ"] = _start->MHz;
		else
			assert(0);
	}
	return kv;
}

void MeasurementInterval::add_string(char * name, char * value)
{
	add_field<std::string>(name, std::string(value));
}

void MeasurementInterval::add_double(char * name, double value)
{
	add_field<double>(name, value);
}

void Measurement::measure()
{
	time = wall_time();
	MHz = theDataCollector->current_nominal_mhz;
}

void MeasurementInterval::start()
{
	_start->measure();
}

void MeasurementInterval::stop()
{
	_end->measure();
}

std::vector<std::string> DataCollector::get_ordered_column_names()
{
	std::vector<std::string> l;
	l.insert(l.end(), tags.begin(), tags.end());
	l.insert(l.end(), stats.begin(), stats.end());
	l.insert(l.end(), calcs.begin(), calcs.end());

#if(0)
	std::cerr << "tags\n";
	for(auto & i: tags) std::cerr << i << ", ";
	std::cerr << "\n";
	std::cerr << "stats\n";
	for(auto & i: stats) std::cerr << i << ", ";
	std::cerr << "\n";
	std::cerr << "calcs\n";
	for(auto & i: calcs) std::cerr << i << ", ";
	std::cerr << "\n";

	std::cerr << "all\n";
	for(auto & i: l) std::cerr << i << ", ";
	std::cerr << "\n";
#endif
	return l;
}

std::string DataCollector::build_csv_row(MeasurementInterval * mi)
{
	json j = mi->build_json();

	std::stringstream out;

	for (auto& n : get_ordered_column_names()) {
		if (mi->kv.find(n) != mi->kv.end()) {
			out << mi->kv[n] << ",";
		} else {
			out << ",";
		}
	}

	out << "\n";
	return out.str();
}

std::string DataCollector::build_csv_header(MeasurementInterval * mi)
{
	json j = mi->build_json();

	std::stringstream out;

	for (auto& n : get_ordered_column_names()) {
		out << rename_stat(n) << ",";
	}

	out << "\n";
	std::cerr << out.str() << "\n";
	return out.str();
}

void DataCollector::set_stat_output_name(const std::string & original_name, const std::string & output_name) {
	output_aliases[original_name] = output_name;
}

std::string DataCollector::rename_stat(const std::string & s) {
	if (output_aliases.find(s) == output_aliases.end()) {
		return s;
	} else {
		return output_aliases[s];
	}
}

json DataCollector::build_json() {
	json j;
	
	for(auto i = stored_intervals.begin();
	    i != stored_intervals.end();
	    i++) {
		json k;
		for (auto& el : (*i)->kv.items()) {
			k[rename_stat(el.key())] = el.value();
		}
		j.push_back(k);
	}
	return j;
}

void DataCollector::write_json(std::ostream & out)
{
	out << build_json().dump(4) << std::endl;  
}

void DataCollector::write_json(const char * filename)
{
	std::fstream out;
	out.open(filename, std::ios_base::out);
	if (out.rdstate())  {
		std::cerr << "Opening " << filename << " failed." << std::endl;
		exit(1);
	}
	write_json(out);
	out.close();
}



void DataCollector::write_csv(const char * filename)
{
	std::fstream out;
	out.open(filename, std::ios_base::out);
	if (out.rdstate())  {
		std::cerr << "Opening " << filename << " failed." << std::endl;
		exit(1);
	}
	write_csv(out);
	out.close();
}
	       
void DataCollector::write_csv(std::ostream & out)
{
	if (stored_intervals.size()) {
		out << build_csv_header(stored_intervals[0]);
		for(auto i = stored_intervals.begin(); i != stored_intervals.end(); i++) {
			out << build_csv_row(*i);
		}
	}
}

void DataCollector::pristine_machine()
{
	flush_caches();
	enable_prefetcher();
	set_cpu_clock_frequency(cpu_frequencies[0]);
  
}

void DataCollector::set_cpu_clock_frequency(int MHz) {
	if (MHz == -1) {
		return;
	}

	current_nominal_mhz = MHz;
	char buf[1024];
	sprintf(buf, "/usr/bin/cpupower frequency-set --freq %dMHz > /dev/null", MHz);
	int r = system(buf);
	if (r != 0) {
		std::cerr << "Couldn't set cpu frequency to " << MHz << "MHz (" << r << ")" << std::endl;

	}
}

void DataCollector::enable_prefetcher(int flags) {

	int cpus = get_nprocs_conf();
	char buf[1024];
	for(int i = 0;i < cpus; i++) {
		//https://software.intel.com/en-us/articles/disclosure-of-hw-prefetcher-control-on-some-intel-processors
		sprintf(buf, "wrmsr -p %d 0x1a4 %d", i, ~flags & 15); // in the register, a 1 disables the register.  So invert and mask out the highorder bits.

		//std::cerr << buf << "\n";
		int r = system(buf);
		if (r != 0) {
			std::cerr << "Couldn't set prefetcher flags or core " << i << " to " << flags << "\n";
		}
	}
}

void DataCollector::disable_prefetcher() {
	enable_prefetcher(0);
}

void DataCollector::flush_caches() {

	if( access( "/dev/cache_control", R_OK|W_OK ) != 0) {
		std::cerr << "Couldn't open '/dev/cache_control'.  Not flushing caches.\n";
		return;
	}  
  
	int fd = open("/dev/cache_control", O_RDWR);
	if (fd == -1) {
		std::cerr << "Couldn't open '/dev/cache_control' to flush caches: " << strerror(errno) << std::endl;
		return;
	}
  
	int r = ioctl(fd, CACHE_CONTROL_FLUSH_CACHES);
	if (r == -1) {
		std::cerr << "Flushing caches failed: " << strerror(errno) << std::endl;
		exit(1);
	}
}


void DataCollector::unknown_stat(const std::string & s) {
	std::cerr << collector_name << " engine cannot record '" << s << "'." << std::endl;
	abort();
}

void DataCollector::write_stats() {
	std::string t = stats_filename + ".raw";
	write_csv(t.c_str());
	std::string cmd = (std::string("calc.py --in ") + t  + " --out " + stats_filename).c_str();
	std::cerr << "calc cmd: " << cmd << "\n";
	system(cmd.c_str());
}
