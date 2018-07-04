(function(){
  "use strict";
  return define(["jquery", "lodash", "js/csrfToken"], function($, _, csrfToken){
    if(window.location.pathname === '/problematicRomanised/'){
      var mkQuery = function(target, data, action){
        return _.extend({
          symbol: $(target).data(data),
          action: action
        }, csrfToken);
      };
      var sendQuery = function(query){
        $.post('.', query).always(function(){
          window.location.reload();
        });
      };
      $('[data-addallowedsymbol]').click(function(){
        var query = mkQuery(this, 'addallowedsymbol', 'add');
        sendQuery(query);
      });
      $('[data-removeallowedsymbol]').click(function(){
        var query = mkQuery(this, 'removeallowedsymbol', 'remove');
        sendQuery(query);
      });
    }
  });
})();
