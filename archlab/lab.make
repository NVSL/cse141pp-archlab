default: submission/code.out

include archlab/compile.make

%.exe : %.o lab_files/main.o
	$(CXX) $^ $(LDFLAGS) -o $@

.PHONY: %.out
%.out : %.exe %.i %.S
	./$< --stats-file $*-stats.csv $(CMD_LINE_ARGS) 2>&1  | tee $@

.PHONY: clean
clean:
	rm -rf *.exe *.o *.i *.S *.out *.d *.gcda *.gcno
	rm -rf lab_files/*.o
	rm -rf submission/*.exe  submission/*.o submission/code.out

