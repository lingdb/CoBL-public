# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    RomanisedSymbol = apps.get_model("lexicon", "RomanisedSymbol")
    allowedRomanised = {
        'a', 'n', '-', 'm', 'i', 's', 'e', 't', '', 'ě', 'b', 'o', 'j', 'l',
        'd', 'v', 'ý', 'r', 'h', 'k', 'š', '̆', 'y', 'u', 'p', 'c', 'ì', 'á',
        '′', 'z', 'ř', 'à', 'ò', 'ž', 'í', 'x', 'č', 'ḁ', 'è', 'f', 'ъ', '̀',
        'é', 'ù', ' ', 'g', 'ä', 'ó', 'w', '̯', 'ɪ', '', 'ï', 'ŋ', '̀', '̥',
        'ə', 'ɣ', 'ú', '́', 'ṡ', 'ç', 'ā', '̣', '(', ')', 'ſ', 'ω', 'ł', 'ę',
        'ß', '[', ']', 'ô', '?', "'", 'ă', 'ġ', 'ẛ', 'ʾ', 'ʒ', '̌', 'ώ', 'ľ',
        'ň', '≠', 'î', 'ṃ', 'û', 'ō', '́', 'ü', 'ḫ', 'ṣ', '̄', 'ū', '/', 'ș',
        'ī', 'ḥ', '*', 'ẓ', 'ë', 'ṭ', 'ś', 'ḯ', 'ĩ', 'K', 'I', 'S', 'N', 'A',
        'æ', 'q', 'ĕ', '̇', 'ḷ', 'V', 'ø', 'H', 'C', 'Z', 'U', 'ċ', 'J', 'ʌ',
        '̃', 'â', 'ː', 'ē', 'ʿ', 'D', 'O', 'M', 'L', 'ê', 'P', 'T', 'ṙ', 'R',
        '̧', 'ʰ', 'ǖ', '˜', 'ḍ', 'ć', 'ñ', 'ǧ', 'ṛ', 'å', 'ė', 'ů', 'E', '͡',
        'G', 'W', 'ö', '~', 'ź', 'ɛ', 'ɜ', 'ț', 'ð', '.', 'B', 'ť', ':', '̐',
        'F', '̲', 'ṇ', 'ɡ', '˳', 'ʊ', 'ǫ', 'ą', 'X', 'ż', 'ũ', 'ḗ', 'ʉ', '″',
        'ď', 'ģ', 'ṅ', '̜', 'ẏ', 'ɨ', 'ŭ', 'β', 'ã', 'ṁ', 'ŕ', 'ǰ', 'ˊ', 'θ',
        'Y', 'þ', 'ļ', '+', 'ŗ', 'õ', 'ɑ', '·', 'ḱ', 'ṓ', 'ń', 'ķ', 'ᵤ', ';',
        'ọ', '=', 'ņ', 'ẽ', 'ṯ', 'ʸ', 'ɔ', '̱', 'ʈ', 'ŵ', 'ᵛ', 'χ', '¬', 'ş',
        'ÿ', 'ȳ', 'ṕ', 'ĭ', '`', '₂', 'ǣ', '̂', '̈́', 'ˤ', 'œ', '̈', 'ˑ', 'ⁱ',
        'ʷ', '&', 'ᴵ', 'ǝ', 'ƕ', 'Q', 'ẖ', 'ǘ', 'į', 'ǔ', 'ε', 'ν', 'ǵ', 'đ',
        'ʎ', '̰', '̊', 'ˈ', 'Š', 'ų', 'Ä', '‑', 'ŷ', 'Ø', 'ŝ', 'ʁ', 'Ī', 'ɸ',
        'ƫ', 'ы', 'к', 'ỹ', 'ɫ', '‘'}
    RomanisedSymbol.objects.bulk_create([
        RomanisedSymbol(symbol=s) for s in allowedRomanised
    ])


def reverse_func(apps, schema_editor):
    RomanisedSymbol = apps.get_model("lexicon", "RomanisedSymbol")
    RomanisedSymbol.objects.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0147_romanisedsymbol')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
