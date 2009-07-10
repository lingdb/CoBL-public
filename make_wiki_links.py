#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage: make_wiki_links.py
"""
def main():
    f = file("language_names_95.csv")
    print "||'''language'''||'''iso'''||'''wals'''||"
    for line in f:
        name, iso, wals = line.rstrip("\n").split("\t")
        line = [""]
        line.append('["%s"]'% name)
        if iso:
            line.append(
            "[http://www.ethnologue.com/show_language.asp?code=%s %s]" %\
            (iso, iso))
        else: 
            line.append("?")
        if wals:
            line.append(wals)
        else:
            line.append("?")
        line.append("")
        print "||".join(line)
    return

if __name__ == "__main__":
    main()
