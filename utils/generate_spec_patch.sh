#!/bin/bash

diff -x MANIFEST -ru ./benchmarks/.pristine_spec2017 ./benchmarks/spec2017 > benchmarks/spec2017-setup/new-spec-CPU2017v1.0.5.patch
