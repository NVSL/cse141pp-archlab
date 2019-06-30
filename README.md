# ArchLab

## Building

Run
```make```

## System Configuration

In order for user-space configuration of clockspeed to work, you need to add 

```intel_pstate=disable```

to the `GRUB_CMDLINE_LINUX` in `/etc/default/grub`.  For example:

```GRUB_CMDLINE_LINUX="console=tty0 console=ttyS1,115200n8 biosdevname=0 net.ifnames=1 intel_pstate=disable"```


## Examples

Try

```
examples/hello_world.exe
```

or

```
examples/random_access.exe
```

## Install Cache Control Kernel Module

```
make setup;
```


