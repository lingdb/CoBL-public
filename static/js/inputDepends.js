(function(){
  "use strict";
  return define(['jquery'], function($){
    //Handling row dependencies:
    $("input[data-dependencyfor-tr]").each(function(){
      var t = $(this);
      //Finding dependant inputs:
      var selector = '[data-inputdepends="'+t.data('dependencyfor-tr')+'"]';
      //May be in a table or in a form.
      var closest = t.closest('tr');
      if(closest.length === 0){
        closest = t.closest('form');
      }
      var dependants = closest.find(selector);
      //Updating dependant inputs:
      var updateDeps = function(enable){
        dependants.each(function(){
          if(enable){
            $(this).removeAttr('disabled');
            if($(this).prop('type') === 'select-one'){
              $(this).css('visibility','');
            }
          }else{
            $(this).attr('disabled','disabled');
            if($(this).prop('type') === 'select-one'){
              $(this).css('visibility','hidden');
              $(this).val("0").change();
            }
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
