from string import uppercase

def int2alpha(n):
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    assert n == int(n)
    assert 1 <= n <= len(codes)
    return codes[n-1]

def alpha2int(a):
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    return codes.index(a)+1

if __name__ == "__main__":
    for i in range(1, 701):
        s = int2alpha(i)
        print i, s
        assert alpha2int(s) == i
