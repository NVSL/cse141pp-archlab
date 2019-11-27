EXAMPLES=run_tests.exe

default: $(EXAMPLES)

USER_CFLAGS=-I$(GOOGLE_TEST_ROOT)/googletest/include
USER_LDFLAGS=-L$(GOOGLE_TEST_ROOT)/lib -lgtest -lgtest_main 
include ../compile.make
../libarchlab/libarchlab.a:
	$(MAKE) -C ../libarchlab

%.exe : %.o  ../libarchlab/libarchlab.a
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@

.PHONY:  test
test: run_tests.exe
	./run_tests.exe --engine papi
