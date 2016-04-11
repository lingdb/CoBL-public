(function(){
  "use strict";
  return define(['jquery','lodash'], function($, _){
    /**
      @param selector :: String | window.Element | $
      @param trigger :: IO ()
      @return filter :: ($ ∧ row) -> Bool
      Returned function is a factory for languageBranches filter.
      It accepts a selector that will be used to identify
      the branch filter buttons and produces a predicate that
      accepts a row and returns true if the row should be hidden.
      The trigger paramter is a callback that will be called
      once a languageBranchesFilter changes.
    */
    return function(selector, trigger){
      //Sanitize selector:
      if(selector instanceof window.Element || _.isString(selector)){
        selector = $(selector);
      }
      //Set to filter with:
      var idSet = {}; // id :: String -> Bool
      /**
        Function to put ids in/out of the idSet.
        The function assumes that either all or none of ids are in idSet.
        @param ids :: [String]
        @return inserted :: Bool
      */
      var changeSet = function(ids){
        if(ids.length === 0) return false;
        if(_.head(ids) in idSet){
          _.each(ids, function(id){delete idSet[id];});
          return false;
        }else{
          _.each(ids, function(id){idSet[id] = true;});
          return true;
        }
      };
      //Binding click handlers:
      selector.find('li').each(function(){
        var el = $(this);
        //Sanitizing ids:
        var ids = el.data('treeids');
        if(_.isString(ids)){
          ids = ids.split(',');
        }else if(_.isNumber(ids)){
          ids = [''+ids];
        }
        if(_.isArray(ids)){
          //Binding click handler:
          el.click(function(){
            var inserted = changeSet(ids);
            if(inserted){
              el.css('opacity', '0.25');
            }else{
              el.css('opacity', '1');
            }
            trigger();
          });
        }else{
          console.log('Unexpected element:', el, typeof(ids), ids);
        }
      });
      //Selector to search rows for:
      var filterSelector = selector.data('selector');
      //Return filter function:
      /**
        @param row :: $ ∧ row
        @return hide :: Bool
      */
      return function(row){
        // Display all if not filtering:
        if(_.keys(idSet).length === 0) return false;
        // Only return false, iff id in idSet:
        var id = row.find(filterSelector).data('languagebranchid');
        if(_.isUndefined(id)) return true;
        if(_.isNumber(id)) id += '';
        return !(id in idSet);
      };
    };
  });
})();
