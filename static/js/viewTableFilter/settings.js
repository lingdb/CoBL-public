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
    var module = {
    };
    (function(){ //Loading session settings:
      var viewIdentifier = _
        .chain(window.location.pathname.split('/'))
        .filter(function(s){ return s.length > 0; })
        .head()
        .value();

      var settings = ('viewTableFilter' in window.sessionStorage) ?
                     JSON.parse(window.sessionStorage.viewTableFilter)
                   : {};

      var extension = {};
      extension[viewIdentifier] = {
        keyupInput: {},
        buttonInput: {},
        sortInput: {}};
      settings = _.extend(extension, settings);

      module.settings = settings[viewIdentifier];
      module.saveSettings = function(){
        window.sessionStorage.viewTableFilter = JSON.stringify(settings);
      };
    })();

    module.storeKeyupInput = function($input, inputClass){
        if(!(inputClass in module.settings.keyupInput)){
          module.settings.keyupInput[inputClass] = {};
        }
        var inputObj = module.settings.keyupInput[inputClass];
        inputObj[$input.data('selector')] = $input.val();
        module.saveSettings();
    };

    module.restoreKeyupInputs = function(){
      _.each(module.settings.keyupInput, function(selectorValMap, inputClass){
        _.each(selectorValMap, function(val, selector){
          if(val === '') return;
          var $input = $('input.'+inputClass+'[data-selector="'+selector+'"]');
          if($input.length > 0){
            $input.val(val);
            $input.trigger('keyup');
          }
        });
      });
    };

    (function(){
      var btnClasses = ['btn-default', 'btn-success', 'btn-danger'];
      // mkStoreKeyupInput for buttons.
      module.storeButtonInput = function($button, inputClass){
        if(!(inputClass in module.settings.buttonInput)){
          module.settings.buttonInput[inputClass] = {};
        }
        var inputObj = module.settings.buttonInput[inputClass];
        _.find(btnClasses, function(cls){
          var has = $button.hasClass(cls);
          if(has){
            inputObj[$button.data('selector')] = cls;
          }
          return has;
        });
        module.saveSettings();
      };

      module.restoreButtonInputs = function(){
        _.each(module.settings.buttonInput, function(selectorValMap, inputClass){
          _.each(selectorValMap, function(val, selector){
            var $button = $('button.'+inputClass+'[data-selector="'+selector+'"]');
            if($button.length > 0){
              $button.removeClass(btnClasses.join(" "));
              $button.addClass(val);
            }
          });
        });
      };
    })();

    module.storeSortInput = function($btn, btnClass){
      var reverse = ($btn.find('.glyphicon-sort-by-attributes').length !== 0);
      var store = {};
      store[btnClass] = {};
      store[btnClass][$btn.data('selector')] = reverse;
      //store = {[btnClass]: {[$btn.data('selector')]: reverse}}
      module.settings.sortInput = store;
      module.saveSettings();
    };

    module.restoreSortInput = function(viewTableFilter){
      /*
      This function needs access to the viewTableFilter module to do it's job.
      That is specifically an object that contains the sort methods.
      */
      _.find(module.settings.sortInput, function(selectorFlagMap, btnClass){
        _.find(selectorFlagMap, function(reverse, selector){
          var $btn = $('.btn.'+btnClass+'[data-selector="'+selector+'"]');
          var table = $btn.closest('table');

          if(!reverse){
            viewTableFilter.updateSortButtons($btn, table);
          }

          var sortFunc = viewTableFilter[btnClass];
          sortFunc($btn, table);

          return true;
        });
        return true;
      });
    };

    module.cleanStorage = function(){
      if ('viewTableFilter' in window.sessionStorage){
        delete window.sessionStorage.viewTableFilter;
        window.location.reload(true);
      }
    };

    return module;
  });
})();
