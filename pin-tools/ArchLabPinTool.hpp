#ifndef ARCH_LAB_PIN_TOOL_INCLUDED
#define ARCH_LAB_PIN_TOOL_INCLUDED

#define PIN_MAX_REGISTERS 32

class ArchLabPinTool {
  const std::string name;
public:
  ArchLabPinTool(std::string  name) : name(name){}
  virtual void start_collection(uint64_t * data) = 0;
  virtual void stop_collection(uint64_t * data) = 0;
  virtual void reset() = 0;
  virtual int get_register_by_name(const char *) = 0;
  virtual const char * get_register_by_index(int i) = 0;

  // This interface is kludgy becausing return std::vectors to the archlab didn't work for some reason.  Perhaps C++ version mismatch.
  virtual void get_available_registers(int * count, char *names[]) = 0;
  const std::string & get_name() {return name;}
};

class DummyPinTool : public ArchLabPinTool {

public:
  DummyPinTool() : ArchLabPinTool("DummyTool") {}
  void start_collection(uint64_t * data){}
  void stop_collection(uint64_t * data){}
  void reset(){}
  int get_register_by_name(const char *){return -1;}
  const char * get_register_by_index(int i){return NULL;}
  void get_available_registers(int * count, char *names[]) {
    *count = 0;
  }

    
};

#define DIRECT_REPLACE(f)			\
  if (RTN_Name(rtn) == #f) {			\
    RTN_Replace(rtn, (AFUNPTR)f);		\
    std::cerr << "Patched " << #f << std::endl;	\
  }

#endif
