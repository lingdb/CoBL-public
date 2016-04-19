(function(){
  "use strict";
  /**
    See if there is a table.viewTableFilter on the site,
    and perform the necessary logic for all .distributionSelection elements.
  */
  return define(['jquery'], function($){
    var table = $('table.viewTableFilter');
    if(table.length !== 1) return;
    console.log('distributionSelection');
    //Ready to go!
    table.find('.distributionSelection').each(function(){
      var $el = $(this),
          inputs = $el.closest('tr').find('.reflectDistribution'),
          handler = function(){
          var wanted = $el.val();
          inputs.each(function(){
            var $i = $(this), allowed = $i.data('allowed');
            if(allowed.indexOf(wanted) >= 0){
              $i.find('input').prop('disabled', false);
            }else{
              $i.find('input').prop('disabled', true);
            }
          });
        };
        $el.change(handler);
        handler.call($el);
    });
  });
})();
