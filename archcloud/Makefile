
TESTS?=.*
.PHONY:  test
test: 
	py.test src/ArchLab/*.py
	bats test.bats -f "$(TESTS)"
