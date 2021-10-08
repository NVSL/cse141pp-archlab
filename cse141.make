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

USER_CFLAGS=-I$(GOOGLE_TEST_ROOT)/googletest/include -I$(CANELA_ROOT)  -I$(BUILD)  -I$(MONETA_ROOT)/moneta/ 

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


LAB_SUBMISSION_DIR?=.
DJR_JOB_ROOT?=.
BUILD?=build/

.PRECIOUS: $(BUILD)%.cpp
.PRECIOUS: $(BUILD)%.hpp
.PRECIOUS: $(BUILD)%.s


#%.so : $(BUILD)%.so
#	cp $< $@

$(BUILD)%.so: $(BUILD)%.o
	$(CXX) $^ $(LDFLAGS) -shared -o $@

$(BUILD)%.cpp: $(LAB_SUBMISSION_DIR)/%.cpp  
	mkdir -p $(BUILD)
	cp $< $@ 

$(BUILD)%.hpp: $(LAB_SUBMISSION_DIR)/%.hpp 
	mkdir -p $(BUILD)
	cp $< $@ 

$(BUILD)%.cpp: %.cpp  
	mkdir -p $(BUILD)
	cp $< $@ 

$(BUILD)%.hpp: %.hpp 
	mkdir -p $(BUILD)
	cp $< $@ 

-include $(wildcard $(BUILD)/*.d)

#$(BUILD)%.inp: $(LAB_SUBMISSION_DIR)/%.inp
#	mkdir -p $(BUILD)
#	cp $< $@

clean: _lab-clean
.PHONY: _lab-clean
_lab-clean:
	rm -rf $(BUILD) .tmp

.PHONY: copy-files
copy-files:
	for i in $(STUDENT_EDITABLE_FILES); do if [ -e $(DJR_JOB_ROOT)/$(LAB_SUBMISSION_DIR)/$$i ]; then (echo Copying $(DJR_JOB_ROOT)/$(LAB_SUBMISSION_DIR)/$$i; cp $(DJR_JOB_ROOT)/$(LAB_SUBMISSION_DIR)/$$i  ./ || true) else true; fi;done


# Build infrastructure
include $(ARCHLAB_ROOT)/compile.make

run_tests.exe: run_tests.o
	$(CXX) $^ $(LDFLAGS) -L$(GOOGLE_TEST_ROOT)/lib -lgtest -lgtest_main  -o $@

# build something
%.exe : 
	$(CXX) $^ $(LDFLAGS) $(EXTRA_LDFLAGS) -o $@


# clean up
.PHONY: clean
clean: lab-clean
lab-clean:
	rm -rf $(CLEANUP)

