(function(){
  "use strict";
  /**
    See if there is a table#viewMeaningLanguages on the site,
    and color it accordingly.
  */
  return define(['jquery','lodash','js/colors'], function($, _, colors){
    var table = $('table#viewMeaningLanguages');
    if(table.length !== 1) return;
    console.log('viewMeaningLanguages');
    var toColor = {colorGroups: [], notFounds: [], alones: []},
        buckets = {}; // :: cText -> [window.Element]
    //Filling buckets and notFounds:
    table.find('tbody > tr').each(function(){
      var cText = $('.cognateClasses', this).text().trim();
      if(cText === ''){
        toColor.notFounds.push(this);
      }else if(cText in buckets){
        buckets[cText].push(this);
      }else{
        buckets[cText] = [this];
      }
    });
    //Distributing buckets into colorGroups and alones:
    _.each(buckets, function(xs){
      if(xs.length === 1){
        toColor.alones.push(xs);
      }else{
        toColor.colorGroups.push(xs);
      }
    });
    //Colorize it!
    colors.colorize(toColor);
  });
})();
