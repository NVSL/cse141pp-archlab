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

.PHONY: starter
starter:
	rm -rf starter-repo
	git clone . starter-repo
	$(MAKE) -C starter-repo remove-private
	(cd starter-repo; git init .; git add * .travis.yml .gitignore; git commit -m "initial import from $$(cd ..; git remote -v)")
	(cd starter-repo; make test)

PRIVATE_FILES=*solution .git private.py test.py

.PHONY: remove-private
remove-private:
	rm -rf $(PRIVATE_FILES)
