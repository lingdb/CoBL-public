from string import uppercase
from ielex.lexicon.models import *

def int2alpha(n):
    """Indexes start at 1!"""
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    assert n == int(n)
    return codes[n-1]

def alpha2int(a):
    """Indexes start at 1!"""
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    return codes.index(a)+1

# cogset_aliases = {}
# for cj in CognateJudgement.objects.all():
#     cogset_aliases.setdefault(cj.lexeme.meaning.gloss,
#             set()).add(cj.cognate_set.id)


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
