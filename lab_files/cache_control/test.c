#include<stdio.h>
#include<cache_control.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/ioctl.h>


int main(int argc, char * argv[]) {

  int fd = open("/dev/cache_control", O_RDWR);
  assert(fd != -1);
  int r = ioctl(fd, CACHE_CONTROL_FLUSH_CACHES);
  assert(r != -1);
  return 0;
}

