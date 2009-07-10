#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage: make_model_tests.py
"""
from __future__ import print_function

def main():
    nexus_template = file("dyen95_template.nex").read()
    sge_template = file("template.sge").read()
    begin = "begin bayesphylogenies;\n  Chains 4;"
    cooling = ("cool", None)
    iterations ="  It 10000000;"
    model = ("m1p", "m2p")
    gamma = ("g4", None)
    covarion = ("cv2", None)
    outgroup = "  Root Albanian_C Albanian_K Albanian_G Albanian_T Albanian_Top ALBANIAN;"
    end = "  Bf emp;\n  pf 10000;\n  autorun;\nend;"
    commands = {"cool":"  Cooling 1000000 -150;",
                "m1p":"  Model m1p;",
                "m2p":"  Model m2p;",
                "g4":"  Gamma 4;",
                "cv2":"  Cv 2;"}

    for parameters in [(a,m,g,c) for a in cooling for m in model for g in gamma
            for c in covarion]:
        block = []
        model = "_".join([p for p in reversed(sorted(parameters)) if p])
        basename = "dyen95_%s" % model
        block.append(begin)
        block.append(iterations)
        for parameter in sorted(parameters):
            if parameter:
                block.append(commands[parameter])
        if "m2p" in parameters:
            block.append(outgroup)
        block.append(end)
        block = "\n".join(block)

        # make files
        print(nexus_template % block, file=file(basename+".nex", "w"))
        print(sge_template % (model, basename+".nex"), 
                file=file(basename+".sge", "w"))
    return

if __name__ == "__main__":
    main()
