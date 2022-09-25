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
	for i in $(STUDENT_EDITABLE_FILES); do if [ -e $(DJR_JOB_ROOT)/$(LAB_SUBMISSION_DIR)/$$i ]; then (cp $(DJR_JOB_ROOT)/$(LAB_SUBMISSION_DIR)/$$i  ./ || true) else true; fi;done


# Build infrastructure
include $(ARCHLAB_ROOT)/compile.make

#run_tests.exe: run_tests.o
#	$(CXX) $^ $(LDFLAGS) -L$(GOOGLE_TEST_ROOT)/lib -lgtest -lgtest_main  -o $@

# build something
%.exe : 
	$(CXX) $^ $(LDFLAGS) $(EXTRA_LDFLAGS) -o $@

%.cpp :%.cpp.encrypted
	cse142-decrypt --in $< --out $@ || echo > $@

#%.cpp.encrypted :%.cpp
#	cse142-encrypt --in $< --out $@ 


.PHONY: decrypt-files
decrypt-files:
	for f in $(ENCRYPTED_FILES); do cse142-decrypt --in $(addsuffix .encrypted,$$f) --out $$f; done

.PHONY: delete-plaintext
delete-plaintext:
	rm -rf $(ENCRYPTED_FILES)

.PHONY: delete-cyphertext
delete-cyphertext:
	rm -rf $(addsuffix .encrypted,$(ENCRYPTED_FILES))


# clean up
.PHONY: clean
clean: lab-clean
lab-clean:
	rm -rf $(CLEANUP)

