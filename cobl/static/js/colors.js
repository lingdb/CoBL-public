(function(){
  "use strict";
  return define(['lodash','jquery'], function(_, $){
    /**
      Colors that supposedly form a maximally dissimilar set.
      Sources:
      https://graphicdesign.stackexchange.com/a/3815/44780
      https://graphicdesign.stackexchange.com/a/3686/44780
      http://godsnotwheregodsnot.blogspot.de/2012/09/color-distribution-methodology.html
      https://github.com/lingdb/IELex2-CognaC/issues/80
    */
    var module = {
      colors: ['#E7CBCB', '#CBE7E7', '#E7D2CB', '#CBE0E7', '#E7D9CB', '#CBD9E7',
               '#E7E0CB', '#CBD2E7', '#E7E7CB', '#CBCBE7', '#E0E7CB', '#D2CBE7',
               '#D9E7CB', '#D9CBE7', '#D2E7CB', '#E0CBE7', '#CBE7CB', '#E7CBE7',
               '#CBE7D2', '#E7CBE0', '#CBE7D9', '#E7CBD9', '#CBE7E0', '#E7CBD2'],
      colorNotFound: '#FFFFFF',
      colorAlone: '#D2D2D2'
    };
    //Computed additions to module:
    module.allColors = _.concat(module.colors, module.colorNotFound, module.colorAlone);
    //Module methods:
    module.colorize = function(o){
      var defaults = {
        colorGroups: [], // :: [[$ | window.Element]]
        notFounds: [],   // :: [$ | window.Element]
        alones: []};     // :: [$ | window.Element]
      //Merging o and defaults:
      o = _.assign(defaults, o);
      //Coloring stuff:
      var colorAll = function(color, xs){
        if(_.isUndefined(color) || _.isUndefined(xs) || xs.length === 0){
          return;
        }
        _.each(xs, function(x){
          if(x instanceof window.Element){
            x = $(x);
          }
          if(x instanceof $){
            x.css('background-color', color);
          }
        });
      };
      _.zipWith(module.colors, o.colorGroups, colorAll);
      colorAll(module.colorNotFound, o.notFounds);
      colorAll(module.colorAlone, o.alones);
    };
    module.findToColor = function(rows, getKey){
      var toColor = {colorGroups: [], notFounds: [], alones: []},
          buckets = {}; // :: cText -> [window.Element]
      //Filling buckets and notFounds:
      rows.each(function(){
        var cText = getKey(this);
        if(!cText){
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
      return toColor;
    };
    //Exporting:
    return module;
  });
})();
