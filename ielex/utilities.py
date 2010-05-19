from string import uppercase
from ielex.lexicon.models import Language

# TODO make this into an infinite generator
codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]

def int2alpha(n):
    """Indexes start at 1!"""
    assert n == int(n)
    return codes[n-1]

def alpha2int(a):
    """Indexes start at 1!"""
    #codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    return codes.index(a)+1

def next_alias(l, ignore=[]):
    """Find the next unused alias from a list of aliases"""
    #codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    for alias in l:
        assert alias in codes+ignore
    for alias in codes:
        if alias not in l+ignore:
            return alias
    return

def renumber_sort_keys():
    # XXX run this function from time to time
    languages = Language.objects.all().order_by("sort_key")
    i = 1.0
    for l in languages:
        l.sort_key = i
        l.save()
        i += 1
    return

if __name__ == "__main__":
    snip_flag = True
    for i in range(1,703):
        s = int2alpha(i)
        if i < 11 or i > 692:
            print i, s
        elif snip_flag:
            print "[...]"
            snip_flag = False
        else:
            pass
        assert alpha2int(s) == i

    l = ["A","B","C"]
    print l
    print "next_alias(l) -->", next_alias(l)
    l = ["none","A","B","C"]
    print l
    print 'next_alias(l, ignore=["none","new"]) -->', next_alias(l,
            ignore=["none","new"])
