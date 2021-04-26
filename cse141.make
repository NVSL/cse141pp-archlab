################
# load lab preliminaries
ifndef ARCHLAB_ROOT
$(error ARCHLAB_ROOT is not set.  Have you sourced config.sh?  Maybe do it again.)
endif
ifndef PIN_ROOT
$(error PIN_ROOT is not set.  Have you sourced config.sh?  Maybe do it again.)
endif
ifndef CANELA_ROOT
$(error CANELA_ROOT is not set.  Have you sourced config.sh?  Maybe do it again.)
endif

include $(ARCHLAB_ROOT)/lab.make


DEBUG?=no

C_OPTS=$(OPTIMIZE)

USER_CFLAGS=-I$(GOOGLE_TEST_ROOT)/googletest/include -I$(CANELA_ROOT) -I./$(BUILD) -I/home/jovyan/work/moneta/


# load user config
include $(BUILD)config.env

# -O4 breaks google test sometimes.
run_tests.o: C_OPTS=-O4 -Wno-unknown-pragmas
run_tests.o: $(BUILD)opt_cnn.hpp
default:
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
ifeq ($(COMPILER),gcc-8)
CC=gcc-8
CXX=g++-8
endif
ifeq ($(COMPILER),gcc-7)
CC=gcc-7
CXX=g++-7
endif


# clean up
.PHONY: clean
clean: lab-clean
lab-clean:
	rm -rf $(CLEANUP)

#  lab test suite.
TESTS?=.*
.PHONY: test test-lab
test-lab:
	(unset LAB_SUBMISSION_DIR; test-lab)
test: test-lab
	if [ -f test.bats ]; then bats test.bats -f '$(TESTS)'; else true;fi

###############
