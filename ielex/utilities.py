from string import uppercase
from ielex.lexicon.models import *

def int2alpha(n):
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    assert n == int(n)
    return codes[n]

def alpha2int(a):
    codes = list(uppercase) + [i+j for i in uppercase for j in uppercase]
    return codes.index(a)

# cogset_aliases = {}
# for cj in CognateJudgement.objects.all():
#     cogset_aliases.setdefault(cj.lexeme.meaning.gloss,
#             set()).add(cj.cognate_set.id)


if __name__ == "__main__":
    for i in range(1, 701):
        s = int2alpha(i)
        print i, s
        assert alpha2int(s) == i
