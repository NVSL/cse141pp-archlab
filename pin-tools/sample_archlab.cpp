/*BEGIN_LEGAL 
Intel Open Source License 

Copyright (c) 2002-2018 Intel Corporation. All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.  Redistributions
in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.  Neither the name of
the Intel Corporation nor the names of its contributors may be used to
endorse or promote products derived from this software without
specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE INTEL OR
ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
END_LEGAL */
/*! @file
 *  This file contains an ISA-portable cache simulator
 *  data cache hierarchies
 */

#include "pin.H"

#include <iostream>
#include <fstream>
#include <cstring>

#include "ArchLabPinTool.hpp"

using std::string;
using std::cerr;
using std::endl;

std::ofstream outFile;
bool tracking = false;

KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE,    "pintool",
    "o", "sample.out", "specify dcache file name");
			    
INT32 Usage()
{
    cerr << "This is a trivial archlab-enabled pin tool.\n\n";
    cerr << KNOB_BASE::StringKnobSummary() << endl; 
    return -1;
}

// libarchlab uses this object to control the pin tool.

class SampleControl : public ArchLabPinTool {
public:
  SampleControl() : ArchLabPinTool("Sample") {}
  void start_collection(uint64_t * data){
  }
  void stop_collection(uint64_t * data){
  }
  void reset(){

  }
  int get_register_by_name(const char *n){
    return 0;
  }
  const char * get_register_by_index(int i){
    return NULL;
  }
  
  void get_available_registers(int * count, char *names[]) {
    *count = 0;
  }
};

ArchLabPinTool * tool = NULL;

// This is the key function.  There's a corresponding function in
// libarchlab that we patch this one.  It allows the pin tool pass the
// `tool` object to archlab.  archlab uses the object to control the pin tool.
ArchLabPinTool * pin_get_tool() {
  return tool;
}

// This does the patching for pin_get_tool()
VOID Routine(RTN rtn, VOID *v)
{
  DIRECT_REPLACE(pin_get_tool);
}

VOID Fini(int code, VOID * v)
{
    // print D-cache profile
    // @todo what does this print
    
  outFile << "Sample pin tool done.\n";
  outFile.close();
}



/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */
    
int main(int argc, char *argv[])
{
    PIN_InitSymbols();

    if( PIN_Init(argc,argv) )
    {
        return Usage();
    }

    outFile.open(KnobOutputFile.Value().c_str());

    tool = new SampleControl();

    RTN_AddInstrumentFunction(Routine, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Never returns

    PIN_StartProgram();
    
    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */
