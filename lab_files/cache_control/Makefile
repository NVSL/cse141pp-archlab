obj-m += cache_control.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

test.exe: test.c
	$(CC) -g -Wall -Werror -I. $< -o $@

.PHONY: test
test: test.exe all
	rmmod cache_control
	insmod cache_control.ko
	./test.exe
	dmesg | tail
	rmmod cache_control
