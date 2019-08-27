/*
 * Copyright 2002-2019 Intel Corporation.
 * 
 * This software is provided to you as Sample Source Code as defined in the accompanying
 * End User License Agreement for the Intel(R) Software Development Products ("Agreement")
 * section 1.L.
 * 
 * This software and the related documents are provided as is, with no express or implied
 * warranties, other than those that are expressly stated in the License.
 */

/*! @file
 *  This file contains an ISA-portable PIN tool for tracing instructions
 */



#include "pin.H"
#include <iostream>
#include <fstream>
#include "ArchLabPinTool.hpp"
using std::cerr;
using std::string;
using std::endl;

/* ===================================================================== */
/* Global Variables */
/* ===================================================================== */

std::ofstream TraceFile;
UINT32 count_trace = 0; // current trace number

bool tracing = false;


class TraceControl : public ArchLabPinTool {
public:
  TraceControl() : ArchLabPinTool("Trace") {}
  void start_collection(uint64_t * data){
    // we don't enable tracing here, because there are too many
    // instructions between and the body of the traced code in the
    // caller.  call archlab_start_tracing() instead.
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

/* Archlab interface */
ArchLabPinTool * tool = NULL;
ArchLabPinTool * pin_get_tool() {
  return tool;
}

void archlab_start_quick() {
  tracing = true;
}
void archlab_stop_quick() {
  tracing = false;
}

VOID Routine(RTN rtn, VOID *v)
{
  DIRECT_REPLACE(pin_get_tool);
  DIRECT_REPLACE(archlab_start_quick);
  DIRECT_REPLACE(archlab_stop_quick);
}



/* ===================================================================== */
/* Commandline Switches */
/* ===================================================================== */

KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool",
    "o", "trace.out", "specify trace file name");
KNOB<BOOL>   KnobCompress(KNOB_MODE_WRITEONCE, "pintool",
    "compress", "0", "Do not compress");
KNOB<BOOL>   KnobTraceFromStart(KNOB_MODE_WRITEONCE, "pintool",
			    "trace_from_start", "0", "Start tracing immediately rather than waiting until measurement is started");

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr <<
        "This tool produces a compressed (dynamic) instruction trace.\n"
        "The trace is still in textual form but repeated sequences\n"
        "of the same code are abbreviated with a number which dramatically\n"
        "reduces the output size and the overhead of the tool.\n"
        "\n";

    cerr << KNOB_BASE::StringKnobSummary();

    cerr << endl;

    return -1;
}


/* ===================================================================== */

VOID  docount(const string *s)
{
    TraceFile.write(s->c_str(), s->size());
    
}

/* ===================================================================== */

VOID Trace(TRACE trace, VOID *v)
{
  if (!tracing) {
    return;
  }
    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
    {
        string traceString = "";
        
        for ( INS ins = BBL_InsHead(bbl); INS_Valid(ins); ins = INS_Next(ins))
        {
            traceString +=  "%" + INS_Disassemble(ins) + "\n";
        }
        

        // we try to keep the overhead small 
        // so we only insert a call where control flow may leave the current trace
        
        if (!KnobCompress)
        {
            INS_InsertCall(BBL_InsTail(bbl), IPOINT_BEFORE, AFUNPTR(docount),
                           IARG_PTR, new string(traceString),
                           IARG_END);
        }
        else
        {
            // Identify traces with an id
            count_trace++;

            // Write the actual trace once at instrumentation time
            string m = "@" + decstr(count_trace) + "\n";
            TraceFile.write(m.c_str(), m.size());            
            TraceFile.write(traceString.c_str(), traceString.size());
            
            
            // at run time, just print the id
            string *s = new string(decstr(count_trace) + "\n");
            INS_InsertCall(BBL_InsTail(bbl), IPOINT_BEFORE, AFUNPTR(docount),
                           IARG_PTR, s,
                           IARG_END);
        }
    }
}

/* ===================================================================== */

VOID Fini(INT32 code, VOID *v)
{
    TraceFile << "# eof" << endl;
    
    TraceFile.close();
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int  main(int argc, char *argv[])
{
    PIN_InitSymbols();
    string trace_header = string("#\n"
                                 "# Compressed Instruction Trace Generated By Pin\n"
                                 "#\n");
    
    
    if( PIN_Init(argc,argv) )
    {
        return Usage();
    }

    tracing = KnobTraceFromStart.Value();
    
    tool = new TraceControl();
      
    TraceFile.open(KnobOutputFile.Value().c_str());
    TraceFile.write(trace_header.c_str(),trace_header.size());

    RTN_AddInstrumentFunction(Routine, 0);        
    TRACE_AddInstrumentFunction(Trace, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Never returns

    PIN_StartProgram();
    
    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */
