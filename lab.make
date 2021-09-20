
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

LAB_NAME=$(shell cat short_name)
STARTER_REPO_NAME_BASE=$(COURSE_INSTANCE)-$(COURSE_NAME)-$(LAB_NAME)
STARTER_REPO_NAME=$(STARTER_REPO_NAME_BASE)-starter
TAG_NAME:=$(STARTER_REPO_NAME)-$(shell date "+%F-%s")
BRANCH_NAME:=$(COURSE_INSTANCE)-starter
STARTER_REPO_URL:=git@github.com:$(GITHUB_CLASSROOM_ORG)/$(STARTER_REPO_NAME).git

.PHONY: release
release: Lab.ipynb

%.ipynb: %.key.ipynb
	nbrelease -I $(NB_RELEASE_INCLUDES) $< -o $@ 


.PHONY: starter-branch	
starter-branch:
	git branch $(BRANCH_NAME) 
	git push -u origin $(BRANCH_NAME)

.PHONY: starter
starter:
	[ $(LAB_NAME) != "" ] # you must set LAB_NAME on the command line: LAB_NAME=foo
	[ "$(shell git rev-parse --abbrev-ref HEAD)" = $(BRANCH_NAME) ] # You need to be on branch for the starter, so you don't merge unwanted changes into the starter.
	rm -rf starter-repo
	git clone . starter-repo
	$(MAKE) -C starter-repo release remove-private
	(name=$$(basename $(PWD));\
	cd starter-repo; \
	git init .; \
	git add Lab.ipynb; \
	git add * .gitignore; \
	git checkout -b main;\
	git branch -r master; \
	echo $(STARTER_REPO_URL) > .starter_repo; git add .starter_repo; \
	git add .starter_repo;\
	git -c user.name='Starter Builder' -c user.email='none@none.org' commit -m "initial import from $$name"\
	)
	@echo "====================================================="
	@echo " 'make push-starter' to create repo "


push-starter:
	[ $(LAB_NAME) != "" ] # you must set LAB_NAME on the command line: LAB_NAME=foo
	echo $(GITHUB_OAUTH_TOKEN) | gh auth login --with-token
	(cd starter-repo;\
	gh config set git_protocol ssh -h github.com; \
	gh repo create --private -y $(GITHUB_CLASSROOM_ORG)/$(STARTER_REPO_NAME); \
	git push --set-upstream origin main;)
	$(MAKE) show-names

.PHONY: show-names
show-names:
	@echo "Assignment Title             : Check Lab.ipynb"
	@echo "Custom repository prefix     : $(STARTER_REPO_NAME_BASE)"
	@echo "Template Repository          : $(GITHUB_CLASSROOM_ORG)/$(STARTER_REPO_NAME)"

update-starter:
	[ $(LAB_NAME) != "" ] # you must set LAB_NAME on the command line: LAB_NAME=foo
	rm -rf fresh_starter
	gh repo clone $(STARTER_REPO_URL) fresh_starter
	$(MAKE) starter 
	cd fresh_starter; rm -rf *; cp -a ../starter-repo/* ../.gitignore .
	cd fresh_starter; git add  $$(cd ../starter-repo; git ls-files --exclude-standard)
	cd fresh_starter; git commit -am "merge in updates"
	cd fresh_starter; git tag -a -m "updates from $$(git rev-parse HEAD)" $(TAG_NAME)
	cd fresh_starter; git push
	cd fresh_starter; git push origin $(TAG_NAME)


_PRIVATE_FILES= *solution .git private.py test.py TA.md admin

.PHONY: remove-private
remove-private:
	rm -rf $(_PRIVATE_FILES) $(PRIVATE_FILES) .travis.yml # Ideally, we would keep this, but right now .travis.yml has my docker_access_token in it.
