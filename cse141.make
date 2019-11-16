################
# load lab preliminaries
include $(ARCHLAB_ROOT)/lab.make

DEBUG?=no

C_OPTS=$(OPTIMIZE)

USER_CFLAGS=-I$(CANELA_ROOT)/googletest/googletest/include -I$(CANELA_ROOT)

# load user config
include $(BUILD)config.env

# -O4 breaks google test sometimes.
run_tests.o: C_OPTS=-O0

regression.out: run_tests.exe
	./run_tests.exe --gtest_output=json:regression.json > $@ || true

# Build infrastructure
include $(ARCHLAB_ROOT)/compile.make

run_tests.exe: run_tests.o
	$(CXX) $^ $(LDFLAGS) -L$(CANELA_ROOT)/googletest/lib -lgtest -lgtest_main  -o $@

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
	rm -rf $(BUILD)/*

#  lab test suite.
.PHONY: test
test: 
	bats test.bats

###############
