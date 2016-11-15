(function(){
  "use strict";
  return define(['jquery'], function($){
    /**
      This module searches for all occurences of 'data-copyrowfrom'
      to treat them as rows that can be copied to from a row
      with the selector given in the attribute.
    */
    $('[data-copyrowfrom]').each(function(){
      var $btn = $(this);
      $btn.click(function(){
        $btn.closest('tr').find('input:visible').each(function(){
          var $input = $(this);
          console.log('Found an input element:', $input.attr('id'));
        });
      });
    });
  });
})();
