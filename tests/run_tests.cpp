#define INCLUDE_TESTS
#define DEBUG_OUTPUT "output/"
#include <iostream>
#include <gtest/gtest.h>


class ArchlabTest : public ::testing::Test {
};

	
int main(int argc, char **argv) {
	::testing::InitGoogleTest(&argc, argv);
	return RUN_ALL_TESTS();
}
