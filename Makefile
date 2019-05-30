PCM = pcm.x
CFLAGS=-Wall -Werror -g -O4 -I. -Ilab_files -I/root/pcm $(USER_CFLAGS) -pthread
CXXFLAGS=$(CFLAGS) -std=gnu++11
LDFLAGS=$(USER_LDFLAGS) -L/root/pcm -lPCM -pthread
ASM_FLAGS=
CPP_FLAGS=

.PRECIOUS: %.o %.exe %.S %.i
.PHONY: default

default: solution/code.out

.PHONY: pcm_submission
pcm_submission: submission/code.pcm
	cp submission/code.pcm ./result.out

%.o : %.cpp
	$(CXX) -c $(CXXFLAGS)  $< -o $@

%.o : %.c
	$(CC) -c $(CFLAGS)  $< -o $@
%.i : %.c
	$(CC) -E -c $(CFLAGS) $(CPP_FLAGS) $< -o $@
%.S : %.c
	$(CC) -S -c $(CFLAGS) $(ASM_FLAGS) -g0 $< -o $@

%.exe : %.o lab_files/main.o lab_files/lab.o
	$(CXX) $^ $(LDFLAGS) -o $@

.PHONY: %.run
%.out : %.exe %.i %.S
	./$< --system-config $*-system.json --stats-file $*-stats.json $(CMD_LINE_ARGS) > $@  2>&1 

#%.pcm: %.exe %.i %.S
#	$(PCM) -- ./$< $(CMD_LINE_ARGS) > $@ 2>&1 > $@ # capture everything.

clean: 
	rm -rf */*.exe */*.o */*.i */*.S */*.out
