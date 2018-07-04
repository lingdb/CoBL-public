(function(){
  "use strict";
  /**
    This module aims to add the datetooltips described in #145
    for every `.datetooltip` that has a `> input`.
  */
  return define(['jquery', 'bootstrap'], function($){
    var computeText = function($input){
      var x = parseInt($input.val(), 10);
      if(x < 2000){
        return 'AD '+(2000-x);
      }else if(x > 2000){
        return (x-2000)+' BC';
      }else if(x === 2000){
        return 'AD 1';
      }
    };
    var withInput = function($datetooltip, λ){
      if($datetooltip.length === 1){
        if($datetooltip.get(0).tagName === 'INPUT'){
          λ($datetooltip);
        }
      }
      $datetooltip.find('input').each(function(){
        λ($(this));
      });
    };
    $('.datetooltip').each(function(){
      var $datetooltip = $(this);
      $datetooltip.attr({
        'data-toggle': 'tooltip',
        "data-placement": "bottom",
        "data-container": "body"
      });
      withInput($datetooltip, function($input){
        $input.change(function(){
          $datetooltip.tooltip('hide')
                      .attr('data-original-title', computeText($input))
                      .tooltip('fixTitle')
                      .tooltip('show');
        });
        $datetooltip.attr('title', computeText($input)).tooltip();
      });
    });
  });
}());
