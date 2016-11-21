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
        var copyDict = {};
        //Gathering source data:
        $($btn.data('copyrowfrom')).find('[data-copyrowfrom-key]').each(function(){
          var $td = $(this);
          copyDict[$td.data('copyrowfrom-key')] = $td.text().trim();
        });
        //Placeing data in target where possible:
        $btn.closest('tr').find('input[data-copyrowfrom-key]').each(function(){
          var $input = $(this),
              key = $input.data('copyrowfrom-key');
          if(key in copyDict){
            $input.val(copyDict[key]);
          }
        });
      });
    });
  });
})();
