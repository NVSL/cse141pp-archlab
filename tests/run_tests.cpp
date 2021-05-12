#include <iostream>
#include <gtest/gtest.h>
#include <archlab.hpp>

class ArchlabTest : public ::testing::Test {
};

volatile bool stop = true;
void sigalrm_handler(int sig)
{
	stop = true;
}

MeasurementInterval & sleep_one() {
	signal(SIGALRM, &sigalrm_handler);  // set a signal handler
	stop = false;
	alarm(1);  // set an alarm
	{
		ArchLabTimer timer; // create it.
		timer.go();
		volatile int i;
		while (!stop) i++;
	}
	auto s = theDataCollector->get_intervals();
	auto & fast = *(s->back());
	fast.build_json();
	return fast;
}

MeasurementInterval & big_scan() {
	const int SIZE = 1024*1024*1024 + 1;
	char * t = new char[SIZE];
	volatile int s = 0;
	for(int i = 0; i < SIZE; i+=64) {
		s+=t[i];
	}
	{
		ArchLabTimer timer;
		timer.go();
		for(int i = 0; i < SIZE; i+=64) {
			s+=t[i+1]; // the +1 ensures that compiler doesn't get clever wrt to the identical loop above.
		}
	}
	auto last = theDataCollector->get_intervals();
	auto & interval = *(last->back());
	interval.build_json();
	return interval;
}

MeasurementInterval & little_scan(bool flush, int count) {
	const int SIZE = 16*1024;
	char * t = new char[SIZE];
	volatile int s = 0;
	{
		ArchLabTimer timer;
		timer.go();
		
		for(int c = 0; c < count; c++) {
			for(int i = 0; i < SIZE; i+=1) {
				s+=t[i];
			}
			if (flush)
				theDataCollector->flush_caches();
		}
	}

	auto last = theDataCollector->get_intervals();
	auto & interval = *(last->back());
	interval.build_json();
	return interval;
}

MeasurementInterval & tiny( int count) {

	volatile int s = 0;
	{
		ArchLabTimer timer;
		timer.go();
		
		for(int c = 0; c < count; c++) {
			s += c;
		}
	}

	auto last = theDataCollector->get_intervals();
	auto & interval = *(last->back());
	interval.build_json();
	return interval;
}


TEST_F(ArchlabTest, cache_flush_test) {
	pristine_machine();
	theDataCollector->disable_prefetcher();
	auto & slow = little_scan(true,10);
	pristine_machine();
	theDataCollector->disable_prefetcher();
	auto & fast = little_scan(false,10);
	
	/*std::cerr << "slow = " << slow.get_kv().dump(4) << "\n";
	std::cerr << "fast = " << fast.get_kv().dump(4) << "\n";
	std::cerr << slow.get_value<float>("ARCHLAB_WALL_TIME") << "\n";
	std::cerr << fast.get_value<float>("ARCHLAB_WALL_TIME") << "\n";*/
	EXPECT_GT(slow.get_value<float>("ARCHLAB_WALL_TIME")/fast.get_value<float>("ARCHLAB_WALL_TIME"),5);
}

TEST_F(ArchlabTest, reset_stats_test) {
	for (int i = 0; i < 10; i++) {
		pristine_machine();
		theDataCollector->disable_prefetcher();
		auto & first = tiny(1000);
		pristine_machine();
		theDataCollector->disable_prefetcher();
		auto & second= tiny(1000);

		//std::cerr << first.get_value<uint64_t>("PAPI_TOT_CYC") << "\n";
		//std::cerr << second.get_value<uint64_t>("PAPI_TOT_CYC") << "\n";
		//std::cerr  << "-----------------\n";
		EXPECT_NEAR(first.get_value<uint64_t>("PAPI_TOT_CYC"),
			    second.get_value<uint64_t>("PAPI_TOT_CYC"),
			    6000);
	}
}

TEST_F(ArchlabTest, prefetcher_test) {
	pristine_machine();
	theDataCollector->disable_prefetcher();
	auto & slow = big_scan();
	pristine_machine();
	theDataCollector->enable_prefetcher();
	auto & fast = big_scan();
	//std::cerr << "slow = " << slow.get_kv().dump(4) << "\n";
	//std::cerr << "fast = " << fast.get_kv().dump(4) << "\n";

	// This seems to show some difference in the number of
	// prefetcher cache misses, so I guess the prefetcher setting
	// is working.  But I don't see any impact on performance...
	EXPECT_LT(slow.get_value<float>("PAPI_PRF_DM"), 100);
	EXPECT_GT(fast.get_value<float>("PAPI_PRF_DM"), 10000);
}

TEST_F(ArchlabTest, cpu_freq_test) {
	// Check whether setting cpu clock works as expected.

	// cpu_frequencies[0] is the highest rate, but that turns on
	// turboboost (I think), so use the second and third highest.
	pristine_machine();
	set_cpu_clock_frequency(cpu_frequencies[1]);
	auto & fast = sleep_one();
	//std::cerr << "fast = " << fast.get_kv().dump(4) << "\n";a
	EXPECT_NEAR(fast.get_value<float>("ARCHLAB_WALL_TIME"), 1, 0.01);

	pristine_machine();
	set_cpu_clock_frequency(cpu_frequencies[2]);
	auto & slow = sleep_one();
	//std::cerr << "slow = " << slow.get_kv().dump(4) << "\n";
	EXPECT_NEAR(slow.get_value<float>("ARCHLAB_WALL_TIME"), 1, 0.01);

	//std::cerr << cpu_frequencies[1] << "\n";
	//std::cerr << cpu_frequencies[2] << "\n";
	EXPECT_NEAR(slow.get_value<float>("PAPI_TOT_CYC"), cpu_frequencies[2]*1000000, 3000000);
	EXPECT_NEAR(slow.get_value<float>("PAPI_TOT_CYC")/
		    fast.get_value<float>("PAPI_TOT_CYC"),
		    (0.0+cpu_frequencies[1])/(0.0+cpu_frequencies[0]), 0.01);
}

int main(int argc, char **argv) {
	::testing::InitGoogleTest(&argc, argv);
	archlab_parse_cmd_line(&argc, argv);
	theDataCollector->track_stat("ARCHLAB_WALL_TIME");
	theDataCollector->register_stat("ARCHLAB_WALL_TIME");

	theDataCollector->track_stat("PAPI_TOT_CYC");
	theDataCollector->register_stat("PAPI_TOT_CYC");

	theDataCollector->track_stat("PAPI_REF_CYC");
	theDataCollector->register_stat("PAPI_REF_CYC");

	theDataCollector->track_stat("PAPI_PRF_DM");
	theDataCollector->register_stat("PAPI_PRF_DM");

	theDataCollector->track_stat("PAPI_L1_LDM");
	theDataCollector->register_stat("PAPI_L1_LDM");

	return RUN_ALL_TESTS();
}
