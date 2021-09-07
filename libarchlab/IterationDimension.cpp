#include "IterationDimension.hpp"
#include <string>
#include <boost/any.hpp>
#include <functional>
#include <iterator>
#include <memory>
#include <algorithm>
#include <vector>
#include "archlab.h"

void re(std::vector<std::shared_ptr<IterationDimension>>::iterator i, std::vector<std::shared_ptr<IterationDimension>>::iterator e, std::function<void()>& inner) {
	if (i != e) {
		std::vector<boost::any> v = (*i)->getValues();
		for (auto iter = v.begin(); iter != v.end(); iter++) {
			((*i)->getFnc())(*iter);
			re(i + 1, e, inner);
			if ((*i)->hasEnding())
				((*i)->getEnding())(*iter);
		}
	}
	else {
		inner();
	}
}

void iterate(std::vector<std::shared_ptr<IterationDimension>> layers, std::function<void()>& inner) {
	re(layers.begin(), layers.end(), inner);
}