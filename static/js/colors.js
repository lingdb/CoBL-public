(function(){
  "use strict";
  return define([], function(){
    /**
      Colors that supposedly form a maximally dissimilar set.
      Sources:
      https://graphicdesign.stackexchange.com/a/3815/44780
      https://graphicdesign.stackexchange.com/a/3686/44780
      http://godsnotwheregodsnot.blogspot.de/2012/09/color-distribution-methodology.html
    */
    var c64 = ['#000000', '#00FF00', '#0000FF', '#FF0000', '#01FFFE', '#FFA6FE', '#FFDB66', '#006401',
               '#010067', '#95003A', '#007DB5', '#FF00F6', '#FFEEE8', '#774D00', '#90FB92', '#0076FF',
               '#D5FF00', '#FF937E', '#6A826C', '#FF029D', '#FE8900', '#7A4782', '#7E2DD2', '#85A900',
               '#FF0056', '#A42400', '#00AE7E', '#683D3B', '#BDC6FF', '#263400', '#BDD393', '#00B917',
               '#9E008E', '#001544', '#C28C9F', '#FF74A3', '#01D0FF', '#004754', '#E56FFE', '#788231',
               '#0E4CA1', '#91D0CB', '#BE9970', '#968AE8', '#BB8800', '#43002C', '#DEFF74', '#00FFC6',
               '#FFE502', '#620E00', '#008F9C', '#98FF52', '#7544B1', '#B500FF', '#00FF78', '#FF6E41',
               '#005F39', '#6B6882', '#5FAD4E', '#A75740', '#A5FFD2', '#FFB167', '#009BFF', '#E85EBE'];

    var c24 = ['#FF0000', '#00FF00', '#E5E500', '#B1B2FF', '#FF00FF', '#00FFFF',
               '#CE0000', '#00BB00', '#BBBB00', '#8585FF', '#D900BE', '#00C5C5',
               '#9F0000', '#008700', '#888800', '#4747FF', '#AD0097', '#009B9B',
               '#630000', '#005700', '#535300', '#0000FF', '#810071', '#007272'];
    //Exporting:
    return {'c64': c64, 'c24': c24};
  });
})();
