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
    module.replacements = {
      // vowels
      'V': '[' + module.vMust + '][' + module.vMay + ']*',
      // consonants
      'C': '[' + module.cMain + module.cOther + module.cAdditional + ']',
      // nasal
      'N': '[' + module.cNasal + module.vNasal + ']',
      // All from lateral {friccative, approx.}
      'FL': '[ɬɮʋɹɻjɰ]',
      // selection by Paul
      'R': '[ʋɹɻʀʁχrɾⱱ˞]',
      // affricate
      'A': '(tʃ|ts|tθ|ʈʂ|dʒ|dz|dð|ɖʐ|pf|bβ|kx|ɡɣ)',
      // fricative, lateral friccative
      'F': '[' + module.fMain + module.fOther + ']',
      // others
      'S': '[' + module.stMain + module.stOther + ']',
      'T': '[' + module.stMain + module.stOther + ']'
    };
    var sanitizeInput = function(input){ // :: String -> String
      _.forEach(module.replacements, function(value, key){
        input = input.replace(new RegExp(key, 'g'), value);
      });
      return input.toLowerCase();
    };
    module.matches = function(input, text){
      // module.matches :: (input :: String, text :: String) -> Bool
      var match = text.replace(/[ˈˌ]/g, '')
                      .match(new Regex(sanitizeInput(input), 'i'));
      return match !== null;
    };
    return module;
  });
})();
