#!/usr/bin/env python
"""There is an error in line 1290 of the original data file. It reads:
b                      209
It should be:
b                      109
"""
# I am handing doubtful cognate classes (i.d. CCNs), but not handling doubtful
# equivalence classes

class CognateClass:

    def __init__(self, meaning, ccn):
        self.name = "%s-%s" % (meaning, ccn)
        self.parents = []
        self.doubtful = False
        self.exclude = False
        self.uninformative = False
        return

    def get_parent(self):
        if self.parents:
            return sorted(self.parents)[0].get_parent()
        else:
            return self

def get_fileobj(filename="iedata.txt"):
    fileobj = file(filename)
    # find beginning of data
    while fileobj.next().rstrip() != "5. THE DATA":
        pass
    fileobj.next()
    return fileobj

def parse():
    """
    usage:
        cognate_class = data["123-001"].get_parent()
    """
    unique = CognateClass(None, None)
    data = {}
    languages = set()
    certain, doubtful = [], []
    for line in get_fileobj():
        line = line.rstrip()
        if line.startswith("a"):
            # meaning = line[2:5]
            meaning = "%03d" % meaning2id[line[6:30].strip()]
        elif line.startswith("b"):
            ccn = line.split()[1]
            cognate_class = CognateClass(meaning, ccn)
            if int(ccn) == 0:
                cognate_class.exclude = True
            elif int(ccn) == 1:
                cognate_class.uninformative = True
            elif 100 <= int(ccn) <= 199:
                cognate_class.doubtful = True
            elif 400 <= int(ccn) <= 499:
                cognate_class.doubtful = True
            try:
                assert cognate_class.name not in data
            except AssertionError:
                print __doc__
                raise
            data[cognate_class.name] = cognate_class
        elif line.startswith("c"):
            ccn1 = "%s-%s" % (meaning, line.split()[1])
            kind = line.split()[2]
            ccn2 = "%s-%s" % (meaning, line.split()[3])
            if kind == "2":
                certain.append((ccn1, ccn2))
            else:
                assert kind == "3"
                doubtful.append((ccn1, ccn2))
        else:
            assert line.startswith(" ")
            # handle lexemes here
    for (parent, child) in set(certain):
        data[child].parents.append(data[parent])

    # results = []
    # for cc in data.values():
    #     n0 = cc.name
    #     n1 = cc.get_parent().name
    #     if n0 == n1:
    #         results.append(n0)
    #     else:
    #         results.append("%s %s" % (n0, n1))
    # for line in sorted(results):
    #     print line

    # # the following confirms that none of the the doubtful CCNs are mapped onto
    # # anything
    # for line in sorted(results):
    #     if line[4] in "14":
    #         print line


    HEADER = ["ID", "source_form", "phon_form", "notes",
                "source", "cognate_class", "reliability",
                "original_cognate_class"]
    output = {}
    for line in get_fileobj():
        line = line.rstrip()
        if line.startswith("a"):
            # meaning = line[2:5]
            meaning = "%03d" % meaning2id[line[6:30].strip()]
        elif line.startswith("b"):
            ccn = line.split()[1]
        elif line.startswith(" "):
            language = line[9:24].strip().replace(" ", "_")
            source_form = line[25:].strip()
            cognate_class = data["%s-%s" % (meaning, ccn)].get_parent()
            original_cognate_class = data["%s-%s" % (meaning, ccn)]
            if cognate_class.doubtful:
                reliability = "C"
            else:
                reliability = "A"
            if cognate_class.uninformative:
                cognate_class.name = ""
            if language not in output:
                output[language] = file("dyen_data/"+language+".csv", "w")
                print >>output[language], "\t".join(HEADER)
            if not cognate_class.exclude:
                print >>output[language], "\t".join([meaning, source_form, "", "",
                    "DyenDB", cognate_class.name, reliability,
                    original_cognate_class.name])
    return

"""Number of parents for non-doubtful sets
0 2470
1 710
2 83
3 27
4 8
5 5
6 3
7 1
8 1
"""
# Dyen Codes {{{
# conversion Dyen form to Ludewig id
meaning2id = {"ALL":1,
"AND":2,
"ANIMAL":3,
"ASHES":4,
"AT":5,
"BACK":6,
"BAD":7,
"BARK (OF A TREE)":8,
"BECAUSE":9,
"BELLY":10,
"BIG":11,
"BIRD":12,
"BLACK":14,
"BLOOD":15,
"BONE":17,
"CHILD (YOUNG)":21,
"CLOUD":22,
"COLD (WEATHER)":23,
"DAY (NOT NIGHT)":27,
"DIRTY":30,
"DOG":31,
"DRY (SUBSTANCE)":33,
"DULL (KNIFE)":34,
"DUST":35,
"EAR":36,
"EARTH (SOIL)":37,
"EGG":39,
"EYE":40,
"FAR":42,
"FAT (SUBSTANCE)":43,
"FATHER":44,
"FEATHER (LARGE)":46,
"FEW":47,
"FIRE":50,
"FISH":51,
"FIVE":52,
"FLOWER":55,
"FOG":57,
"FOOT":58,
"FOUR":59,
"FRUIT":61,
"GOOD":64,
"GRASS":65,
"GREEN":66,
"GUTS":67,
"HAIR":68,
"HAND":69,
"HE":70,
"HEAD":71,
"HEART":73,
"HEAVY":74,
"HERE":75,
"HOLD (IN HAND)":77,
"HOW":79,
"HUSBAND":81,
"I":82,
"ICE":83,
"IF":84,
"IN":85,
"KNOW (FACTS)":88,
"LAKE":89,
"LEAF":91,
"LEFT (HAND)":92,
"LEG":93,
"LIVER":96,
"LONG":97,
"LOUSE":98,
"MAN (MALE)":99,
"MANY":100,
"MEAT (FLESH)":101,
"MOTHER":103,
"MOUNTAIN":104,
"MOUTH":105,
"NAME":106,
"NARROW":107,
"NEAR":108,
"NECK":109,
"NEW":110,
"NIGHT":111,
"NOSE":112,
"NOT":113,
"OLD":114,
"ONE":115,
"OTHER":116,
"PERSON":117,
"RED":122,
"RIGHT (CORRECT)":123,
"RIGHT (HAND)":124,
"RIVER":125,
"ROAD":126,
"ROOT":127,
"ROPE":128,
"ROTTEN (LOG)":129,
"RUB":131,
"SALT":132,
"SAND":133,
"SCRATCH (ITCH)":135,
"SEA (OCEAN)":136,
"SEED":138,
"SHARP (KNIFE)":140,
"SHORT":141,
"SKIN (OF PERSON)":144,
"SKY":145,
"SMALL":147,
"SMOKE":149,
"SMOOTH":150,
"SNAKE":151,
"SNOW":152,
"SOME":153,
"STAR":159,
"STICK (OF WOOD)":160,
"STONE":161,
"STRAIGHT":162,
"SUN":164,
"TAIL":167,
"THAT":168,
"THERE":169,
"THEY":170,
"THICK":171,
"THIN":172,
"THIS":174,
"THOU":175,
"THREE":176,
"TO BITE":13,
"TO BLOW (WIND)":16,
"TO BREATHE":19,
"TO BURN (INTRANSITIVE)":20,
"TO COME":24,
"TO COUNT":25,
"TO CUT":26,
"TO DIE":28,
"TO DIG":29,
"TO DRINK":32,
"TO EAT":38,
"TO FALL (DROP)":41,
"TO FEAR":45,
"TO FIGHT":48,
"TO FLOAT":53,
"TO FLOW":54,
"TO FLY":56,
"TO FREEZE":60,
"TO GIVE":63,
"TO HEAR":72,
"TO HIT":76,
"TO HUNT (GAME)":80,
"TO KILL":86,
"TO LAUGH":90,
"TO LIE (ON SIDE)":94,
"TO LIVE":95,
"TO PLAY":118,
"TO PULL":119,
"TO PUSH":120,
"TO RAIN":121,
"TO SAY":134,
"TO SEE":137,
"TO SEW":139,
"TO SING":142,
"TO SIT":143,
"TO SLEEP":146,
"TO SMELL (PERCEIVE ODOR)":148,
"TO SPIT":154,
"TO SPLIT":155,
"TO SQUEEZE":156,
"TO STAB (OR STICK)":157,
"TO STAND":158,
"TO SUCK":163,
"TO SWELL":165,
"TO SWIM":166,
"TO THINK":173,
"TO THROW":177,
"TO TIE":178,
"TO TURN (VEER)":182,
"TO VOMIT":184,
"TO WALK":185,
"TO WASH":187,
"TONGUE":179,
"TOOTH (FRONT)":180,
"TREE":181,
"TWO":183,
"WARM (WEATHER)":186,
"WATER":188,
"WE":189,
"WET":190,
"WHAT":191,
"WHEN":192,
"WHERE":193,
"WHITE":194,
"WHO":195,
"WIDE":196,
"WIFE":197,
"WIND (BREEZE)":198,
"WING":199,
"WIPE":200,
"WITH (ACCOMPANYING)":201,
"WOMAN":202,
"WOODS":203,
"WORM":204,
"YE":205,
"YEAR":206,
"YELLOW":207,
# forms not in Dyen
"BREAST":18,
"FINGERNAIL":49,
"FULL":62,
"HORN":78,
"KNEE":87,
"MOON":102,
"ROUND":130,
}
# }}}


if __name__ == "__main__":
    parse()
