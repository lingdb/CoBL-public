(function(){
  "use strict";
  return define([], function(){
    /**
      Colors that supposedly form a maximally dissimilar set.
      Sources:
      https://graphicdesign.stackexchange.com/a/3815/44780
      https://graphicdesign.stackexchange.com/a/3686/44780
      http://godsnotwheregodsnot.blogspot.de/2012/09/color-distribution-methodology.html
      https://github.com/lingdb/IELex2-CognaC/issues/80
    */
    var cs = ['#E7CBCB', '#CBE7E7', '#E7D2CB', '#CBE0E7', '#E7D9CB', '#CBD9E7',
              '#E7E0CB', '#CBD2E7', '#E7E7CB', '#CBCBE7', '#E0E7CB', '#D2CBE7',
              '#D9E7CB', '#D9CBE7', '#D2E7CB', '#E0CBE7', '#CBE7CB', '#E7CBE7',
              '#CBE7D2', '#E7CBE0', '#CBE7D9', '#E7CBD9', '#CBE7E0', '#E7CBD2'],
        cNotFound = '#FFFFFF',
        cAlone = '#D2D2D2';
    //Exporting:
    return {
      colors: cs,
      colorNotFound: cNotFound,
      colorAlone: cAlone
    };
  });
})();
