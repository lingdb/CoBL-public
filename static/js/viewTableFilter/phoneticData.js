(function(){
  "use strict";
  return define(['lodash'], function(_){
    var module = {
      symbolGroups: {
        // All from vowels section
        vMust: 'iyɨʉɯuɪʏʊeøɘɵɤoəɛœɜɞʌɔæɐaɶɑɒɚɝ',
        // All from tone
        vMay: '˥˦˧˨˩↓↑↗↘̋́̄̀̏᷈᷅᷄̂̌ˈˌːˑ̆|‖.‿̃˔̟̹̜̠̝˕˞̞̰̤̥̈̽',
        // All from consonants main
        cMain: 'pbtdʈɖɟɟkɡqɢʔmɱnɳɲŋɴʙrʀⱱɾɽɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮʋɹɻjɰlɭʎʟɫ',
        // All from consonants other
        cOther: 'ʼɓɗʄɠʛʘǀǃǂǁʍʡʬ¡wɕʭǃ¡ɥʑʪʜɺʫʢɧʩ',
        // ː from vowels
        cAdditional: 'ː',
        // From consonants all in nasal row.
        cNasal: 'mɱnɳɲŋɴ',
        // ~ from vowels nasalised
        vNasal: '̃',
        // [Lateral-]Fricative from consonants main
        fMain: 'ɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮ',
        // Selection from consonants other
        fOther: 'ɕʑɧ',
        // All in plosive from consonants main
        stMain: 'pbtdʈɖɟɟkɡqɢʔ',
        // All in voiced, imposives and clicks from consonants other
        stOther: 'ɓɗʄɠʛʘǀǃǂǁ'
      }
    };
    module.replacements = (function(s){
      return {
        // vowels
        'V': '[' + s.vMust + '][' + s.vMay + ']*',
        // consonants
        'C': '[' + s.cMain + s.cOther + s.cAdditional + ']',
        // nasal
        'N': '[' + s.cNasal + s.vNasal + ']',
        // All from lateral {friccative, approx.}
        'FL': '[ɬɮʋɹɻjɰ]',
        // selection by Paul
        'R': '[ʋɹɻʀʁχrɾⱱ˞]',
        // affricate
        'A': '(tʃ|ts|tθ|ʈʂ|dʒ|dz|dð|ɖʐ|pf|bβ|kx|ɡɣ)',
        // fricative, lateral friccative
        'F': '[' + s.fMain + s.fOther + ']',
        // others
        'S': '[' + s.stMain + s.stOther + ']',
        'T': '[' + s.stMain + s.stOther + ']'
      };
    })(module.symbolGroups);
    var sanitizeInput = function(input){ // :: String -> String
      _.forEach(module.replacements, function(value, key){
        input = input.replace(new RegExp(key, 'g'), value);
      });
      return input.toLowerCase();
    };
    module.matches = function(input, text){
      // module.matches :: (input :: String, text :: String) -> Bool
      var match = text.replace(/[ˈˌ]/g, '')
                      .match(new RegExp(sanitizeInput(input), 'i'));
      return match === null;
    };
    return module;
  });
})();
