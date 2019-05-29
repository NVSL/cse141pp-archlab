PCM = pcm.x
CFLAGS=-Wall -Werror -g -O4 $(USER_CFLAGS)
LDFLAGS=$(USER_LDFLAGS)
ASM_FLAGS=
CPP_FLAGS=

.PRECIOUS: %.o %.exe %.S %.i
.PHONY: default

default: solution/code.out

.PHONY: pcm_submission
pcm_submission: submission/code.out

%.o : %.c
	$(CC) -c $(CFLAGS)  $< -o $@
%.i : %.c
	$(CC) -E -c $(CFLAGS) $(CPP_FLAGS) $< -o $@
%.S : %.c
	$(CC) -S -c $(CFLAGS) $(ASM_FLAGS) -g0 $< -o $@

%.exe : %.o lab_files/main.o
	$(CC) $(LD_FLAGS) $^ -o $@

.PHONY: %.run
%.out : %.exe %.i %.S
	./$< $(CMD_LINE_ARGS) > $@  2>&1 

%.pcm: %.exe %.i %.S
	$(PCM) -- ./$< $(CMD_LINE_ARGS) > $@ 2>&1 > $@ # capture everything.

clean: 
	rm -rf */*.exe */*.o */*.i */*.S */*.out
