LAB_SUBMISSION_DIR?=.
BUILD?=build/

.PRECIOUS: $(BUILD)%.cpp
.PRECIOUS: $(BUILD)%.hpp

$(BUILD)%.cpp: $(LAB_SUBMISSION_DIR)/%.cpp
	mkdir -p $(BUILD)
	cp $< $@

$(BUILD)%.hpp: $(LAB_SUBMISSION_DIR)/%.hpp
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
	@echo "make push-starter :  Create repo and push"

STARTER_REPO_NAME_BASE=$(COURSE_INSTANCE)-$(COURSE_NAME)-$(shell runlab --info short_name)
STARTER_REPO_NAME=$(STARTER_REPO_NAME_BASE)-starter
TAG_NAME:=$(STARTER_REPO_NAME)-$(shell date "+%F-%s")
BRANCH_NAME:=$(TAG_NAME)-branch
STARTER_REPO_URL:=https://github.com/$(GITHUB_CLASSROOM_ORG)/$(STARTER_REPO_NAME).git

.PHONY: starter
starter:
	rm -rf starter-repo
	git clone . starter-repo
	$(MAKE) -C starter-repo remove-private
	(name=$$(basename $(PWD));\
	cd starter-repo; \
	git init .; \
	git add * .gitignore; \
	echo $(STARTER_REPO_URL) > .starter_repo; git add .starter_repo; \
	git add .starter_repo;\
	git -c user.name='Starter Builder' -c user.email='none@none.org' commit -m "initial import from $$name"\
	)
#	(cd starter-repo; make test-lab)
	@echo "====================================================="
	@echo "              Starter repo seems to work             "
	@echo " 'make push-starter' to create repo "


push-starter:
	curl -H "Authorization: token $(GITHUB_OAUTH_TOKEN)" https://api.github.com/orgs/$(GITHUB_CLASSROOM_ORG)/repos -d "{\"name\":\"$(STARTER_REPO_NAME)\", \"private\":\"false\", \"visibility\": \"public\", \"is_template\":\"true\"}" -X POST > starter.json
	! jextract errors < starter.json 2>/dev/null || (echo "Repo creation failed:"; cat starter.json; false)
	(cd starter-repo; git remote add origin $(STARTER_REPO_URL))
	(cd starter-repo; git push -u origin master)
	git tag -a -m "starter repo: $(STARTER_REPO_NAME)" $(TAG_NAME)
	git branch $(BRANCH_NAME)	
	git push -u origin $(BRANCH_NAME)
	git push origin $(TAG_NAME)
	@echo "Assignment Title             : $$(runlab --info lab_name)"
	@echo "Custom repository prefix     : $(STARTER_REPO_NAME_BASE)"
	@echo "Template Repository          : $(GITHUB_CLASSROOM_ORG)/$(STARTER_REPO_NAME)"

update-starter:
	git clone $(STARTER_REPO_URL)
	make starter 
	cd $(STARTER_REPO_NAME); rm -rf *; cp -r ../starter-repo/* .
	git commit -am "merge in updates";
	git tag -a -m "updates from $$(git rev-parse HEAD)" $(TAG_NAME)
	git push
	git push origin $(TAG_NAME)

PRIVATE_FILES=*solution .git private.py test.py TA.md admin

.PHONY: remove-private
remove-private:
	rm -rf $(PRIVATE_FILES) .travis.yml # Ideally, we would keep this, but right now .travis.yml has my docker_access_token in it.
