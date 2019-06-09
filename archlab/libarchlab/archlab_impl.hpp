#ifndef ARCH_LAB_IMPL_HPP_INCLUDED
#define ARCH_LAB_IMPL_HPP_INCLUDED

#ifdef __cplusplus
// Some C++ utilities
#include <json.hpp>
using json = nlohmann::json;


class ArchLabTimer {
  json kv;
  bool timing;
public:
  ArchLabTimer(): timing(false) {
  }

  ~ArchLabTimer();
  
  template<class T>
  ArchLabTimer & attr(const std::string &name, const T & value) {
    kv[name] = value;
    return *this;
  }

  void go(); 
  void go(std::function<void(void)> f);
  
};


template<class T>
class SIInt {
  typedef T type;
  
public:
  T _value;

  SIInt & operator= (const SIInt &s) {
    _value = s._value;
    return *this;
  }
    
  SIInt() : _value(0) {}
  SIInt(const T v): _value(v) {}
  SIInt(int & v): _value(v) {}
  SIInt(const int & v): _value(v) {}
  operator T() const {return _value;}

  const type &value() const {
    return _value;
  }
  
};

template<class T>
std::ostream &operator<<( std::ostream &output, const SIInt<T> &i ) {
  output << i._value;
  return output;
}

template<class T>
std::istream &operator>>( std::istream  &input, SIInt<T> &i ) {
  std::string t;
  input >> t;
  i._value = si_parse(t.c_str());
  return input;
}

typedef SIInt<uint64_t> si_uint64_t;
#endif

#endif
