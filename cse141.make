################
# load lab preliminaries
include $(ARCHLAB_ROOT)/lab.make

DEBUG?=no

C_OPTS=$(OPTIMIZE)

USER_CFLAGS=-I$(GOOGLE_TEST_ROOT)/googletest/include -I$(CANELA_ROOT) -I./$(BUILD)


# load user config
include $(BUILD)config.env

# -O4 breaks google test sometimes.
run_tests.o: C_OPTS=-O0
run_tests.o: $(BUILD)opt_cnn.hpp

regression.out: run_tests.exe
	./run_tests.exe --gtest_output=json:regression.json > $@ || true

# Build infrastructure
include $(ARCHLAB_ROOT)/compile.make

run_tests.exe: run_tests.o
	$(CXX) $^ $(LDFLAGS) -L$(GOOGLE_TEST_ROOT)/lib -lgtest -lgtest_main  -o $@

# build something
%.exe : $(BUILD)%.o main.o
	$(CXX) $^ $(LDFLAGS) -o $@

ifeq ($(COMPILER),gcc-9)
CC=gcc-9
CXX=g++-9
endif


# clean up
.PHONY: clean
clean: lab-clean
lab-clean:
	rm -rf $(CLEANUP)

#  lab test suite.
TESTS?=.*
.PHONY: test
test: 
	bats test.bats  -f '$(TESTS)'

###############
