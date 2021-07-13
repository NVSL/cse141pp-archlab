obj-m += cache_control.o

ONLY_IF_VALID=! [ -d /lib/modules/$(shell uname -r) ] ||
all:
	$(ONLY_IF_VALID) make -C /lib/modules/$(shell uname -r)/build M=$(shell pwd) modules
setup: all
clean:
	$(ONLY_IF_VALID) make -C /lib/modules/$(shell uname -r)/build M=$(shell pwd) clean
modules_install:
	$(ONLY_IF_VALID) make -C /lib/modules/$(shell uname -r)/build M=$(shell pwd) modules_install

test.exe: test.c
	$(CC) -g -Wall -Werror -I. $< -o $@

.PHONY: test
test: test.exe all
	-rmmod cache_control
	insmod cache_control.ko
	./test.exe
	dmesg | tail
	rmmod cache_control
