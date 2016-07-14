(function(){
  "use strict";
  return define(['jquery'], function($){
    //Handling row dependencies:
    $("input[data-dependencyfor-tr]").each(function(){
      var t = $(this);
      //Finding dependant inputs:
      var selector = 'input[data-inputdepends="'+t.data('dependencyfor-tr')+'"]';
      var dependants = t.closest('tr').find(selector);
      //Updating dependant inputs:
      var updateDeps = function(enable){
        dependants.each(function(){
          if(enable){
            $(this).removeAttr('disabled');
          }else{
            $(this).attr('disabled','disabled');
          }
        });
      };
      if(t.attr('type') === 'checkbox'){
        //Handling the magic:
        var handler = function(){ updateDeps(t.is(':checked')); };
        t.click(handler);
        handler();
      }
    });
  });
})();
