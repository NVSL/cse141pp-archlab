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

TEST_F(ArchlabTest, cpu_freq_tests) {

	theDataCollector->track_stat("ARCHLAB_WALL_TIME");
	theDataCollector->register_stat("ARCHLAB_WALL_TIME");

	theDataCollector->track_stat("PAPI_TOT_CYC");
	theDataCollector->register_stat("PAPI_TOT_CYC");

	theDataCollector->track_stat("PAPI_REF_CYC");
	theDataCollector->register_stat("PAPI_REF_CYC");

	// Check whether setting cpu clock works as expected.
	// cpu_frequencies[0] is the highest rate, but that turns on
	// turboboost (I think), so use the second and third highest.
	pristine_machine();
	set_cpu_clock_frequency(cpu_frequencies[1]);
	auto & fast = sleep_one();
	//std::cerr << "fast = " << fast.get_kv().dump(4) << "\n";
	EXPECT_NEAR(fast.get_value<float>("ARCHLAB_WALL_TIME"), 1, 0.01);

	pristine_machine();
	set_cpu_clock_frequency(cpu_frequencies[2]);
	auto & slow = sleep_one();
	//std::cerr << "slow = " << slow.get_kv().dump(4) << "\n";
	EXPECT_NEAR(slow.get_value<float>("ARCHLAB_WALL_TIME"), 1, 0.01);

	//std::cerr << cpu_frequencies[1] << "\n";
	//std::cerr << cpu_frequencies[2] << "\n";
	EXPECT_NEAR(slow.get_value<float>("PAPI_TOT_CYC"), cpu_frequencies[2]*1000000, 2000000);
	EXPECT_NEAR(slow.get_value<float>("PAPI_TOT_CYC")/
		    fast.get_value<float>("PAPI_TOT_CYC"),
		    (0.0+cpu_frequencies[1])/(0.0+cpu_frequencies[0]), 0.01);
}

int main(int argc, char **argv) {
	::testing::InitGoogleTest(&argc, argv);
	archlab_parse_cmd_line(&argc, argv);

	return RUN_ALL_TESTS();
}
