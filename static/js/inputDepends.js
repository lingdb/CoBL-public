(function(){
  "use strict";
  return define(['jquery'], function($){
    //Handling row dependencies:
    $("input[data-dependencyfor-tr]").each(function(){
      var t = $(this);
      //Finding dependant inputs:
      var selector = '[data-inputdepends="'+t.data('dependencyfor-tr')+'"]';
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
      var handler; // var used below
      if(t.attr('type') === 'checkbox'){
        //Handling the magic:
        handler = function(){ updateDeps(t.is(':checked')); };
        t.click(handler);
        handler();
      }else if(t.attr('type') === 'text'){
        //Handling the magic:
        handler = function(){ updateDeps(t.val() !== ''); };
        t.keyup(handler);
        handler();
      }
    });
  });
})();
