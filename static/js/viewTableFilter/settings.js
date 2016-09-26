(function(){
  "use strict";
  return define(['jquery', 'lodash'],
                function($, _){
    //Tool to return:
    //Module data:
    /**
      This module aims to provide settings to viewTableFilter
      so that we can restore given filters when navigating pages.
    */
    var module = {};
    (function(){ //Loading session settings:
      var settings = ('viewTableFilter' in window.sessionStorage) ?
                     JSON.parse(window.sessionStorage.viewTableFilter)
                   : {};
      module.settings = _.extend({keyupInput: {}}, settings);
    })();

    module.saveSettings = function(){
      window.sessionStorage.viewTableFilter = JSON.stringify(module.settings);
    };
    /*
      Factory for functions to update sessionStorage
      for a given $('input.'+inputClass).
    */
    module.mkStoreKeyupInput = function($input, inputClass){
        return function(){
          if(!(inputClass in module.settings)){
            module.settings.keyupInput[inputClass] = {};
          }
          var inputObj = module.settings.keyupInput[inputClass];
          inputObj[$input.data('selector')] = $input.val();
          module.saveSettings();
        };
    };

    module.restoreKeyupInputs = function(){
      _.each(module.settings.keyupInput, function(selectorValMap, inputClass){
        _.each(selectorValMap, function(val, selector){
          var $input = $('input.'+inputClass+'[data-selector="'+selector+'"]');
          if($input.length > 0){
            $input.val(val);
            $input.trigger('keyup');
          }
        });
      });
    };

    return module;
  });
})();
