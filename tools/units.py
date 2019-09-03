
def s(x):
    return x * 1.0
def ms(x): 
    return x * 1e-3 * 1.0
def us(x):
    return x * 1e-6 * 1.0
def ns(x):
    return x * 1e-9 * 1.0
def ps(x):
    return x * 1e-12 * 1.0

def GHz(x):
    return x * 1e9 * 1.0
def MHz(x):
    return x * 1e6 * 1.0
def kHz(x):
    return x * 1e3 * 1.0
def Hz(x):
    return x*1.0

def TiB(x):
    return x * 2**40 * 1.0
def GiB(x):
    return x * 2**30 * 1.0
def MiB(x):
    return x * 2**20 * 1.0
def kiB(x):
    return x * 2**10 * 1.0
def B(x):
    return x * 1.0

def TB(x):
    return x * 1000**4 * 1.0
def GB(x):
    return x * 1000**3 * 1.0
def MB(x):
    return x * 1000**2 * 1.0
def kB(x):
    return x * 1000**1 * 1.0

def Tbit(x):
    return x * 10**12 / 8.0
def Gbit(x):
    return x * 10**9 / 8.0
def Mbit(x):
    return x * 10**6 / 8.0
def kbit(x):
    return x * 10**3 / 8.0
def bit(x):
    return x / 8.0

def Tera(x):
    return x * 1000**4 * 1.0
def Giga(x):
    return x * 1000**3 * 1.0
def Mega(x):
    return x * 1000**2 * 1.0
def kilo(x):
    return x * 1000**1 * 1.0
def one(x):
    return x * 1.0
def milli(x): 
    return x * 1e-3 * 1.0
def micro(x):
    return x * 1e-6 * 1.0
def nano(x):
    return x * 1e-9 * 1.0
def pico(x):
    return x * 1e-12 * 1.0


def formatter(l):
    def F(x):
        for b in l:
            if x < b[0]:
                o = "{}{}".format(round(x/b[1](1),1),b[2])
                return o
        assert False, "Can't format {}".format(x)
    return F
    
T = formatter([(ns(1), ps, "ps"),
              (us(1),  ns, "ns"),
              (ms(1),  us, "us"),
              (s(1),   ms, "ms"),
              (1e20,   s,  "s")])

count = formatter([(nano(1), pico,  "p"),
                   (micro(1),nano,  "n"),
                   (milli(1),micro, "u"),
                   (one(1),  milli, "m"),
                   (kilo(1), one,   ""),
                   (Mega(1), kilo,  "k"),
                   (Giga(1), Mega,  "M"),
                   (Tera(1), Giga,  "G"),
                   (1e20,    Tera,  "T")])

sci = formatter([(nano(1), pico,  "e-12"),
                 (micro(1),nano,  "e-9"),
                 (milli(1),micro, "e-6"),
                 (one(1),  milli, "e-3"),
                 (kilo(1), one,   ""),
                 (Mega(1), kilo,  "e3"),
                 (Giga(1), Mega,  "e6"),
                 (Tera(1), Giga,  "e9"),
                 (1e20,    Tera,  "e12")])

BW_b2 = formatter([(kiB(1), lambda x:x, ""),
               (MiB(1), kiB, "kiB/s"),
               (GiB(1), MiB, "MiB/s"),
               (TiB(1), GiB, "GiB/s"),
               (1e20,  TiB, "TiB/s")])

BW_b2_as_b10 = formatter([(kiB(1), lambda x:x, ""),
               (MiB(1), kiB, "kB/s"),
               (GiB(1), MiB, "MB/s"),
               (TiB(1), GiB, "GB/s"),
               (1e20,  TiB, "TB/s")])

BW_b10 = formatter([(kB(1), lambda x:x, ""),
               (MB(1), kB, "kB/s"),
               (GB(1), MB, "MB/s"),
               (TB(1), GB, "GB/s"),
               (1e20,  TB, "TB/s")])

Rate = formatter([(kilo(1), one, "/s"),
                  (Mega(1), kB,  "k/s"),
                  (Giga(1), MB,  "M/s"),
                  (Tera(1), GB,  "G/s"),
                  (1e20,    TB,  "T/s")])

def BW(x, base=2):
    if base == 2:
        return BW_b2(x)
    elif base == 10:
        return BW_b10(x)
    elif base == "2-as-10":
        return BW_b2_as_b10(x)
    else:
        raise Exception("Illegal format base {}".format(base))

Bytes = formatter([(kiB(1), lambda x:x, ""),
                   (MiB(1), kiB, "kiB"),
                   (GiB(1), MiB, "MiB"),
                   (TiB(1), GiB, "GiB"),
                   (1e20,  TiB, "TiB")])

def Percent(v):
    return("{}%".format(str(round(v*100.0,2))))

def Speedup(v):
    return("{}x".format(str(round(v,2))))

def raw(x):
    return x
