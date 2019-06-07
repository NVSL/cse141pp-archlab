#ifndef DCACHE_ARCH_LAB_INCLUDED
#define DCACHE_ARCH_LAB_INCLUDED

#define PIN_REGISTERS				\
  REG(DCACHE_HITS)				\
  REG(DCACHE_MISSES)				\
  REG(DCACHE_LOAD_HITS)				\
  REG(DCACHE_LOAD_MISSES)			\
  REG(DCACHE_STORE_HITS)			\
  REG(DCACHE_STORE_MISSES)

const char * archlab_pin_registers[] = {
#define REG(x) #x,
  PIN_REGISTERS
  NULL
#undef REG
};

typedef enum{
#define REG(x) x##_EVENT,
  PIN_REGISTERS
} pin_register_index_t;

#endif
