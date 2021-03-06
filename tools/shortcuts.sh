BRANCH_BREAKDOWN="./archlab_run --engine papi --stat PAPI_TOT_CYC --stat PAPI_BR_INS --stat PAPI_BR_PRC --stat PAPI_TOT_INS --stat UOPS_RETIRED"
PIPELINE_BREAKDOWN="./archlab_run --engine papi --stat PAPI_TOT_CYC --stat UOPS_RETIRED --stat IDQ:ALL_MITE_UOPS --stat UOPS_EXECUTED --stat PAPI_TOT_INS"

PIN_INST_MIX="$PIN_ROOT/pin -follow-execv 1 -t $ARCHLAB_ROOT/pin-tools/obj-intel64/catmix.so -o $PWD/BENCHMARK_LABEL.mix -- "

/home/root/cse141pp-archlab/benchmarks/spec2017/

export ARCHLAB_RUNNER="$PWD/../../tools/archlab_run --engine papi --stat-set PE.cfg --stats-file PWD/BENCHMARK_LABEL.csv --tag opt=0 --tag BENCHMARK_LABEL --"
