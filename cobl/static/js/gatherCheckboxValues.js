(function(){
  "use strict";
  return define(['jquery', 'lodash'], function($, _){
    /**
      This module exports a fuction that takes a selector and
      and returns an array containing all input values
      that are ':checked'.
      @param selector :: String | window.Element | $
    */
    return function(selector){
      if(_.isString(selector) || selector instanceof window.Element){
        selector = $(selector);
      }
      var ret = [];
      selector.each(function(){
        var input = $(this);
        if(input.is(':checked')){
          ret.push(input.val());
        }
      });
      return ret;
    };
  });
})();
