#include "archlab.hpp"
#include "IterationDimension.hpp"
#include <boost/any.hpp>
#include <stdio.h>
#include <memory>

using namespace std;

int main(int argc, char *argv[]) {
	int x,y,z,v;
    
    shared_ptr<IterationDimension> param1_dim(new IterationDimensionT<int>("param1", "1",
					      "Parameter 1 value.  Pass multiple values to run with multiple values.", true, 1, [&](int param1_value) 
	{	
		x = param1_value;
        theDataCollector->register_tag(param1_dim->getParaName(), param1_value);
		std::cout << "Setting param1_value (" << param1_dim->getParaName() << ") = " << param1_value <<"\n";
	}));

	shared_ptr<IterationDimension> param2_dim(new IterationDimensionT<int>("param2", "1",
					      "Parameter 2 value.  Pass multiple values to run with multiple values.", true, 1, [&](int param2_value) 
	{	
		y = param2_value;
        theDataCollector->register_tag(param2_dim->getParaName(), param2_value);
		std::cout << "Setting param2_value (" << param2_dim->getParaName() << ") = " << param2_value <<"\n";
	}));
    
	shared_ptr<IterationDimension> param3_dim(new IterationDimensionT<int>("param3", "1",
					      "Parameter 3 value.  Pass multiple values to run with multiple values.", true, 1, [&](int param3_value) 
	{	
		z = param3_value;
        theDataCollector->register_tag(param3_dim->getParaName(), param3_value);
		std::cout << "Setting param3_value (" << param3_dim->getParaName() << ") = " << param3_value <<"\n";
	}));

    function<void()> volume = [&](){
        pristine_machine();               // reset the machine 
        start_timing("tag", "volume",      // Start timing.  Set an identifier 'tag' = 'hello'.  It'll appear along with the measurements in 'stats.csv'
                NULL);
        for(int i = 0; i < x; i++)
            for(int j = 0; j < y; j++)
                for(int k = 0; k < z; k++)
                    v += 1;
        stop_timing();                    // Stop timing.
        archlab_write_stats();
    };

    archlab_parse_cmd_line(&argc, argv);

    vector<shared_ptr<IterationDimension>> dimensions = { param1_dim, param2_dim, param3_dim };
    
    iterate(dimensions, volume);

    printf("Now, `cat stats.csv` will show you the results.\n");
    return 0;
}

