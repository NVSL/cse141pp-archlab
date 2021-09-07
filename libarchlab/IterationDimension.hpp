#ifndef ITERATION_DIMENSION_INCLUDED
#define ITERATION_DIMENSION_INCLUDED
#include <string>
#include <boost/any.hpp>
#include <functional>
#include <iterator>
#include <memory>
#include <algorithm>
#include <vector>
#include "archlab.h"

class IterationDimension {
public:
	virtual std::vector<boost::any> getValues() = 0;
	virtual std::function<void(boost::any)> getFnc() = 0;
	virtual std::function<void(boost::any)> getEnding() = 0;
	virtual bool hasEnding() = 0;
	virtual void add_option() = 0;
	virtual boost::any getOriginVals() = 0;
	virtual std::string getParaName() = 0;
};

template<class T>
class IterationDimensionT : public IterationDimension {
private:
	std::string name;
	std::vector<T> def;
	std::string default_string;
	std::string desc;
	bool normalPara;
	T default_push;
	std::string param_name;
	std::vector<T> values;
	std::function<void(T)> fnc;
	std::function<void(T)> ending;
	bool has_ending;
public:
	IterationDimensionT(std::string n, std::string def_s, std::string des_s, bool np, T def_p, std::function<void(T)> f) {
		name = n;
		fnc = f;
		ending = [&](T i) {};
		has_ending = false;
		default_string = def_s;
		desc = des_s;
		normalPara = np;
		default_push = def_p;
		this->add_option();
	}
	IterationDimensionT(std::string n, std::string def_s, std::string des_s, bool np, T def_p, std::function<void(T)> f, std::function<void(T)> e) {
		name = n;
		fnc = f;
		ending = e;
		has_ending = true;
		default_string = def_s;
		desc = des_s;
		normalPara = np;
		default_push = def_p;
		this->add_option();
	}

	std::vector<boost::any> getValues() {
		std::vector<boost::any> out;
		out.resize(values.size());
		std::transform(values.begin(), values.end(), out.begin(), [&](T i) {return i; });
		return out;
	}

	std::function<void(boost::any)> getFnc() {
		std::function<void(boost::any)> out = [&](boost::any p) {fnc(boost::any_cast<T>(p)); };
		return out;
	}

	std::function<void(boost::any)> getEnding() {
		std::function<void(boost::any)> out = [&](boost::any p) {ending(boost::any_cast<T>(p)); };
		return out;
	}

	bool hasEnding() {
		return has_ending;
	}

	void add_option(){
		def.push_back(default_push);
		archlab_add_multi_option<std::vector<T>>(name, values, def, default_string, desc);
		if(normalPara) {
			archlab_add_option<std::string>(name + "-name",
			param_name,
			name,
			"Name for " + name);
		}
	}
	
	boost::any getOriginVals(){
		return &values;
	}

	std::string getParaName(){
		return param_name;
	}
};

void re(std::vector<std::shared_ptr<IterationDimension>>::iterator i, std::vector<std::shared_ptr<IterationDimension>>::iterator e, std::function<void()>& inner);

void iterate(std::vector<std::shared_ptr<IterationDimension>> layers, std::function<void()>& inner);

#endif