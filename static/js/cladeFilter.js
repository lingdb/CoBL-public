(function(){
  "use strict";
  return define(['jquery','lodash'], function($, _){
    /**
      @param triggerFilter :: IO ()
      @return λ :: ($ ∧ row -> Bool) | null
      This function provides clade filtering
      and aims to be integrated in viewTableFilter.
      To achieve this this module provides a factory that takes
      a `triggerFilter` callback.
      The callback will be used to instruct viewTableFilter
      that another filter pass is necessary.
      If setup for the factory succeeds, a filter function will be returned.
      Otherwise null will be returned and filtering won't be possible.
    */
    return function(triggerFilter){
      var cladeFilter = $('#cladeFilter');
      if(cladeFilter.length !== 1){
        return null; //Not activating filter.
      }
      //Loading session settings:
      var settings = ('cladeFilter' in window.sessionStorage) ?
                     JSON.parse(window.sessionStorage.cladeFilter)
                   : {representative: false, // :: Bool
                      cladepaths: {} // :: cladepath -> 0
                     };
      //Function to save settings to the session:
      var saveSettings = function(){
        window.sessionStorage.cladeFilter = JSON.stringify(settings);
      };
      /**
        @param li :: $ ∧ li
        @param initial :: Bool
        Handling clicks on <li>.
        initial implies that li won't be altered.
      */
      var handleLi = function(li, initial){
        var representative = li.data('cladefilter-representative');
        var cladepath = li.data('cladefilter-cladepath');
        //Alter settings:
        if(initial === false){
          if(!_.isUndefined(representative)){
            settings.representative = !settings.representative;
          }else if(!_.isUndefined(cladepath)){
            if(cladepath in settings.cladepaths){
              delete settings.cladepaths[cladepath];
            }else{
              settings.cladepaths[cladepath] = 0;
            }
          }
          saveSettings();
        }
        //Check if we should grey out:
        var grey = false;
        if(!_.isUndefined(representative)){
          grey = settings.representative;
        }else if(!_.isUndefined(cladepath)){
          grey = cladepath in settings.cladepaths;
        }
        //Adjust style:
        li.css('opacity', (grey === true) ? 0.25 : 1);
      };
      //Bind buttons:
      cladeFilter.find('li').each(function(){
        var li = $(this);
        handleLi(li, true);
        li.click(function(){
          handleLi(li, false);
          triggerFilter();
        });
      });
      //Filter function that must decide if a row should be hidden:
      return function(row){
        var representative = row.data('cladefilter-representative');
        var cladepath = row.data('cladefilter-cladepath');
        // Filter representative:
        if(!_.isUndefined(representative)){
          if(settings.representative && representative === 'True'){
            return true;
          }
        }
        // Filter cladepath:
        if(!_.isUndefined(cladepath)){
          return _.some(_.keys(settings.cladepaths), function(prefix){
            return _.startsWith(cladepath, prefix);
          });
        }
        //Default is not to hide:
        return false;
      };
    };
  });
})();
