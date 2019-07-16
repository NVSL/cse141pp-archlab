#-*- Makefile -*-
ARCHLAB=$(ARCHLAB_ROOT)
PCM_ROOT=$(ARCHLAB)/pcm
PAPI_ROOT=/usr/local
PIN_ROOT=$(ARCHLAB)/pin
export PIN_ROOT
C_OPTS ?= -O3
CFLAGS ?=-Wall -Werror -g $(C_OPTS) -I. -I$(PCM_ROOT) -pthread -I$(ARCHLAB)/libarchlab -I$(ARCHLAB) -I$(PAPI_ROOT)/include $(USER_CFLAGS) -I../
CXXFLAGS ?=$(CFLAGS) -std=gnu++11
LDFLAGS ?= $(USER_LDFLAGS)  -L$(PAPI_ROOT)/lib -L$(ARCHLAB)/libarchlab -L$(PCM_ROOT) -pthread -larchlab -static -lPCM -lpapi -lboost_program_options
ASM_FLAGS=
CPP_FLAGS=
.PRECIOUS: %.o %.exe %.s %.i
.PHONY: default

default:


%.o : %.s
	$(CC) -c $(CFLAGS) $(ASM_FLAGS) -g0 $< -o $@

%.o : %.cpp
	$(CXX) -c $(CXXFLAGS)  $< -o $@

%.o : %.c
	$(CC) -c $(CFLAGS)  $< -o $@

%.i : %.cpp
	$(CXX) -E -c $(CXXFLAGS) $(CPP_FLAGS) $< -o $@
%.i : %.c
	$(CC) -E -c $(CFLAGS) $(CPP_FLAGS) $< -o $@

%.s : %.cpp
	$(CXX) -S -c $(CXXFLAGS) $(ASM_FLAGS) -g0 $< -o - |c++filt > $@
%.s : %.c
	$(CC) -S -c $(CFLAGS) $(ASM_FLAGS) -g0 $< -o $@

%.trace.s: %.trace
	cp $< $@

%.d: %.c
	 @set -e; rm -f $@; \
         $(CC) -MM $(CXXFLAGS) $< > $@.$$$$; \
         sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; \
         rm -f $@.$$$$

%.d: %.cpp
	@set -e; rm -f $@; \
         $(CXX) -MM $(CXXFLAGS) $< > $@.$$$$; \
         sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; \
         rm -f $@.$$$$

### Rules for the rename-x86

RENAME_FLAGS?= 

.PRECIOUS: %.gv

%.gv %.csv: %.s
	rename-x86.py --dot $*.gv --csv $*.csv $(RENAME_FLAGS) < $< 

%-gv.pdf: %.gv
	dot -Tpdf $< > $@ || rm -rf $@


rename-clean:
	rm -rf *.gv *-gv.pdf *.csv

clean: rename-clean


.PHONY: %.out
%.out : %.exe %.i %.s
	./$< --stats-file $*-stats.csv $(CMD_LINE_ARGS) 2>&1  | tee $@

.PHONY: archlab-clean
archlab-clean:
	rm -rf *.exe *.o *.i *.s *.out *.d *.gcda *.gcno

clean: archlab-clean
