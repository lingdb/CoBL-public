from ielex.lexicon.models import Language

def local_iso_code_generator():
    """Yield as-yet unused codes from the reserved local range (qaa-qtz)"""
    known_iso_codes = Language.objects.values_list("iso_code", flat=True)
    letters = "abcdefghijklmnopqrstuvwxyz"
    for second_letter in letters[:letters.index("t")]:
        for third_letter in letters:
            code = "q%s%s" % (second_letter, third_letter)
            if code not in known_iso_codes:
                yield code

def nexus_comment(s):
    lines = s.split("\n")
    maxlen = max(len(e) for e in lines)
    return "\n".join("[ "+e.ljust(maxlen)+" ]" for e in lines)

