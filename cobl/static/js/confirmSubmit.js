(function(){
  "use strict";
  /*
    This module searches for .confirmSubmit[data-confirm] elements.
    Such elements are expected to be placed in a form
    that has an input[type="submit"].
    If the .confirmSubmit is clicked, data-confirm is displayed as a message.
    If the resulting dialog is confirmed, the form is submitted.
  */
  return define(['jquery','bootbox'],
                function($, bootbox){
    var module = {
      buttonSelector: ".confirmSubmit[data-confirm]",
      submitSelector: 'input[type="submit"]'
    };
    module.init = function(){
      $(module.buttonSelector).click(function(){
        var $btn = $(this);
        bootbox.confirm($btn.data('confirm'), function(result){
          if(result === true){
            $btn.closest('form').find(module.submitSelector).trigger('click');
          }
        });
      });
    };
    return module;
  });
})();
