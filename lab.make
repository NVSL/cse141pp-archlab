include $(ARCHLAB_ROOT)/compile.make
.PHONY: remove-solution
remove-solution:
	rm -rf $(SOLUTION_FILES)

.PHONY: lab-help
help: lab-help

lab-help:
	@echo "make remove-solution : Remove solution files."
