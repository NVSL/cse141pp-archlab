include $(ARCHLAB_ROOT)/compile.make

LAB_SUBMISSION_DIR?=.
BUILD?=build

$(BUILD)/%.cpp: $(LAB_SUBMISSION_DIR)/%.cpp
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)/%.hpp: $(LAB_SUBMISSION_DIR)/%.hpp
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)/config: $(LAB_SUBMISSION_DIR)/config
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)/config.mk: $(BUILD)/config
	cp $< $@

clean:lab-clean
.PHONY: lab-clean
lab-clean:
	rm -rf $(BUILD)

ifeq ($(DEVEL_MODE),yes)
CMD_LINE_ARGS=$(LAB_DEVEL_CMD_LINE) $(USER_CMD_LINE)
else
CMD_LINE_ARGS=$(LAB_RUN_CMD_LINE) $(USER_CMD_LINE)
endif

.PHONY: lab-help
help: lab-help

lab-help:
