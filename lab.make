default: submission/code.out

include archlab/compile.make

%.exe : %.o lab_files/main.o  archlab
	$(CXX) $(filter %o,$^) $(LDFLAGS) -o $@

.PHONY: archlab
archlab:
	$(MAKE) -C archlab

.PHONY: %.out
%.out : %.exe %.i %.S
	./$< --stats-file $*-stats.csv $(CMD_LINE_ARGS) 2>&1  | tee $@

.PHONY: clean
clean: archlab-clean
	rm -rf lab_files/*.o
	rm -rf submission/*.exe  submission/*.o submission/code.out

