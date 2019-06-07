PCM = pcm.x
CFLAGS=-Wall -Werror -g -O0 -I. -Ilab_files -I/root/pcm $(USER_CFLAGS) -pthread -I../papi-5.7.0/install/include
CXXFLAGS=$(CFLAGS) -std=gnu++11
LDFLAGS=$(USER_LDFLAGS)  -L../papi-5.7.0/install/lib  -L/root/pcm -pthread -lPCM -lpapi -static
ASM_FLAGS=
CPP_FLAGS=

.PRECIOUS: %.o %.exe %.S %.i
.PHONY: default



default: submission/code.out

.PHONY: pcm_submission
pcm_submission: submission/code.pcm
	cp submission/code.pcm ./result.out

%.o : %.cpp
	$(CXX) -c $(CXXFLAGS)  $< -o $@

%.o : %.c
	$(CC) -c $(CFLAGS)  $< -o $@

%.i : %.cpp
	$(CXX) -E -c $(CXXFLAGS) $(CPP_FLAGS) $< -o $@
%.i : %.c
	$(CC) -E -c $(CFLAGS) $(CPP_FLAGS) $< -o $@

%.S : %.cpp
	$(CXX) -S -c $(CXXFLAGS) $(ASM_FLAGS) -g0 $< -o - |c++filt > $@
%.S : %.c
	$(CC) -S -c $(CFLAGS) $(ASM_FLAGS) -g0 $< -o $@

%.exe : %.o lab_files/main.o lab_files/archlab.o lab_files/microbenchmarks.o lab_files/DataCollector.o lab_files/PCMDataCollector.o lab_files/PAPIDataCollector.o lab_files/PINDataCollector.o
	$(CXX) $^ $(LDFLAGS) -o $@

.PHONY: %.out
%.out : %.exe %.i %.S
	./$< --stats-file $*-stats.csv $(CMD_LINE_ARGS) 2>&1  | tee $@

#%.pcm: %.exe %.i %.S
#	$(PCM) -- ./$< $(CMD_LINE_ARGS) > $@ 2>&1 > $@ # capture everything.

clean: 
	rm -rf */*.exe */*.o */*.i */*.S */*.out
