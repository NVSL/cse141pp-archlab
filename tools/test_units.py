import pytest
from units import *

def test_MB():
    assert MiB(1) % 1024 == 0

def test_B():
    assert MiB(1) / kiB(1) == 1024
    assert kiB(1) == 1024
    assert BW(kiB(1)) == "1.0kiB/s"
    assert BW(kiB(1024)) == "1.0MiB/s"

    print(BW(TiB(1), base=10))
    assert BW(TiB(1), base=2) == "1.0TiB/s"
    assert BW(TiB(1), base=10) == "1.1TB/s"
    assert BW(TiB(1), base="2-as-10") == "1.0TB/s"


    assert BW(TB(1), base=2) == "931.3GiB/s"
    assert BW(TB(1), base=10) == "1.0TB/s"
    assert BW(TB(1), base="2-as-10") == "931.3GB/s"

def test_count():
    assert count(1) == "1.0"
    assert count(1000.0) == "1.0k"
    assert count(0.1) == "100.0m"
    assert count(1000000.0) == "1.0M"

def test_sci():
    assert sci(1) == "1.0"
    assert sci(1000.0) == "1.0e3"
    assert sci(0.1) == "100.0e-3"
    assert sci(1000000.0) == "1.0e6"

def test_T():
    assert s(1)/ms(1) == 1000

def test_bits():
    assert Mbit(8) / MiB(1) <= 1, "Mbits are base 10."
