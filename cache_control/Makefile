obj-m += cache_control.o

EFFECTIVE_UNAME?=$(shell uname -r)

ONLY_IF_VALID=! [ -d /lib/modules/$(EFFECTIVE_UNAME) ] ||
all:
	$(ONLY_IF_VALID) make -C /lib/modules/$(EFFECTIVE_UNAME)/build M=$(shell pwd) modules
setup: all
clean:
	$(ONLY_IF_VALID) make -C /lib/modules/$(EFFECTIVE_UNAME)/build M=$(shell pwd) clean
modules_install:
	$(ONLY_IF_VALID) make -C /lib/modules/$(EFFECTIVE_UNAME)/build M=$(shell pwd) modules_install

test.exe: test.c
	$(CC) -g -Wall -Werror -I. $< -o $@

.PHONY: test
test: test.exe all
	-rmmod cache_control
	insmod cache_control.ko
	./test.exe
	dmesg | tail
	rmmod cache_control
