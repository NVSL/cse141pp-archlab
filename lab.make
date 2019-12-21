LAB_SUBMISSION_DIR?=.
BUILD?=build/

$(BUILD)%.cpp: $(LAB_SUBMISSION_DIR)/%.cpp
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)%.hpp: $(LAB_SUBMISSION_DIR)/%.hpp
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)config: $(LAB_SUBMISSION_DIR)/config
	mkdir -p $(BUILD)
	cp $< $@


$(BUILD)config.env: $(LAB_SUBMISSION_DIR)/config.env
	mkdir -p $(BUILD)
	cp $< $@


$(BUILD)%.inp: $(LAB_SUBMISSION_DIR)/%.inp
	mkdir -p $(BUILD)
	cp $< $@

clean: _lab-clean
.PHONY: _lab-clean
_lab-clean:
	rm -rf $(BUILD) .tmp

# The build infrastructure wants a install target.
.PHONY: install
install:

#ifeq ($(DEVEL_MODE),yes)
#CMD_LINE_ARGS=$(LAB_DEVEL_CMD_LINE) $(USER_CMD_LINE)
#else
#CMD_LINE_ARGS=$(LAB_RUN_CMD_LINE) $(USER_CMD_LINE)
#endif

.PHONY: lab-help
help: lab-help

lab-help:
	@echo "make build-starter:  Build a starter repo"

.PHONY: build-starter
build-starter:
	git clone . starter-repo
	$(MAKE) -D starter-repo remove-private

PRIVATE_FILES=*solution .git

.PHONY: remove-private
remove-private:
	rm -rf $(PRIVATE_FILES)
	strip-lab lab.py
	strip-travis .travis.yml
