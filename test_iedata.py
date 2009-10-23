#!/usr/bin/env python
"""
sets to test:

MOTHER

c                         200  3  204
b                      205
c                         204  2  205
  097 65 Khaskura        AMA
  097 64 Nepali List     AMA

Khaskura and Nepali should have the same class, and it should be cognate class
A if we're conflating doubtful classes.

Likewise,

Ukrainian       MATY, NEN'KA
Greek D         MANA, MAMA, METERA
Afrikaans       MOEDER, MA
Albanian G    AMA, MOMA, NANA    B
Albanian C    MEM                A
Albanian K    MEME               A
Albanian T    NENE               A <- should be B
Albanian Top  NENE               B
"""
from pprint import pprint
import iedata
data = iedata.parse()
for language in ["Ukrainian", "Greek D", "Afrikaans", "Khaskura",
        "Nepali List", "Albanian K", "Albanian K", "Albanian T",
        "Albanian Top"]:
    print language, "MOTHER", data[language.replace(" ","_")]["MOTHER"]

pprint(iedata.doubtful_classes())
print len(iedata.doubtful_classes())

# # FATHER
# 
# CODES = [001, 002, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 400, 210,
#         211, 212, 213, 214, 215, 216, 217]
# 
# # equiv {{{
# equiv = """\
# 200  2  201
# 200  2  202
# 200  2  206
# 200  2  201
# 201  3  202
# 201  3  203
# 201  3  204
# 201  3  205
# 201  3  206
# 201  3  207
# 201  3  208
# 201  3  209
# 201  3  400
# 200  2  202
# 201  3  202
# 202  2  203
# 202  3  204
# 202  3  205
# 202  3  206
# 202  3  207
# 202  3  208
# 202  3  209
# 202  3  400
# 201  3  203
# 202  2  203
# 203  3  204
# 203  3  205
# 203  3  206
# 203  3  207
# 203  3  208
# 203  3  209
# 203  3  400
# 201  3  204
# 202  3  204
# 203  3  204
# 204  3  205
# 204  3  206
# 204  3  207
# 204  3  208
# 204  3  209
# 204  3  400
# 201  3  205
# 202  3  205
# 203  3  205
# 204  3  205
# 205  3  206
# 205  3  207
# 205  3  208
# 205  3  209
# 205  3  400
# 200  2  206
# 201  3  206
# 202  3  206
# 203  3  206
# 204  3  206
# 205  3  206
# 206  2  207
# 206  3  208
# 206  3  209
# 206  3  400
# 201  3  207
# 202  3  207
# 203  3  207
# 204  3  207
# 205  3  207
# 206  2  207
# 207  3  208
# 207  3  209
# 207  3  400
# 201  3  208
# 202  3  208
# 203  3  208
# 204  3  208
# 205  3  208
# 206  3  208
# 207  3  208
# 208  3  209
# 208  3  400
# 201  3  209
# 202  3  209
# 203  3  209
# 204  3  209
# 205  3  209
# 206  3  209
# 207  3  209
# 208  3  209
# 209  3  400
# 209  2  210
# 209  2  211
# 209  2  213
# 209  2  216
# 201  3  400
# 202  3  400
# 203  3  400
# 204  3  400
# 205  3  400
# 206  3  400
# 207  3  400
# 208  3  400
# 209  3  400
# 209  2  210
# 210  2  211
# 210  2  213
# 210  2  216
# 209  2  211
# 210  2  211
# 211  3  212
# 211  2  213
# 211  3  214
# 211  3  215
# 211  2  216
# 211  3  212
# 212  3  213
# 212  3  214
# 212  3  215
# 209  2  213
# 210  2  213
# 211  2  213
# 212  3  213
# 213  3  214
# 213  3  215
# 213  2  216
# 211  3  214
# 212  3  214
# 213  3  214
# 214  3  215
# 211  3  215
# 212  3  215
# 213  3  215
# 214  3  215
# 209  2  216
# 210  2  216
# 211  2  216
# 213  2  216
# 216  3  217
# 216  3  217""" #}}}
# 
# 
# ssets, dsets = {}, {}
# for line in equiv.split("\n"):
#     row = [int(i) for i in line.strip().split()]
#     if row[1] == 2:
#         sset1, sset2 = row[0], row[2]
#         if sset1 in ssets:
#             sset1 = ssets[sset1]
#         ssets[sset2] = sset1
#     elif row[1] == 3:
#         dset1, dset2 = row[0], row[2]
#         if dset1 in dsets:
#             dset1 = dsets[dset1]
#         dsets[dset2] = dset1
# print ssets
# print sorted(set(ssets.keys()))
# print sorted(set(ssets.values()))
# print dsets
# print sorted(set(dsets.keys()))
# print sorted(set(dsets.values()))


# vim:fdm=marker
