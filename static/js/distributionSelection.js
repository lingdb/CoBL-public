(function(){
  "use strict";
  /**
    See if there is a $root.view$rootFilter on the site,
    and perform the necessary logic for all .distributionSelection elements.
  */
  return define(['jquery'], function($){
    var $root = $('table.viewTableFilter');
    if($root.length === 0){
      $root = $('form .distributionSelection');
      if($root.length === 0){
        return;
      }else{
        $root = $($root.get(0)).closest('form');
      }
    }
    //Method to find closest tr or form
    var findClosest = function($el){
      var $closest = $el.closest('tr');
      if($closest.length === 0){
        $closest = $el.closest('form');
      }
      return $closest;
    };
    //Ready to go!
    $root.find('.distributionSelection').each(function(){
      var $el = $(this),
          inputs = findClosest($el).find('.reflectDistribution'),
          handler = function(){
          var wanted = $el.val();
          inputs.each(function(){
            var $i = $(this), allowed = $i.data('allowed');
            var isWanted = allowed.indexOf(wanted) >= 0;
            var toChange = this.tagName === 'INPUT' ? $i : $i.find('input');
            toChange.prop('disabled', !isWanted);
          });
        };
        $el.change(handler);
        handler.call($el);
    });
  });
})();
