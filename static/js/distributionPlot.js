(function(){
  "use strict";
  /**
    See if there is a table.distributionPlot on the site,
    and perform the necessary setup.

    This code shall follow a loose FRP principle.
    For each row:
    * We check the distribution, both initially and on change.
    * We gather the distribution data so that it's ready to plot:
      - initially
      - On distribution change
      - On change of any value
    * We plot the distribution(s) in a (special) div using c3.
  */
  return define(['jquery','lodash','c3'], function($, _, c3){
    var table = $('table.distributionPlot');
    if(table.length !== 1) return;
    /***/
    var nameDistributionMap = {};
    /**
    Function to compute distribution data.
      $el :: $('select'), expected length === 1
      $inputs :: $('tr.reflectDistribution')
      color :: string
      name :: string
    */
    var computeDistribution = function($el, $inputs, color, name){
      //Distribution object to compute:
      var distribution = {name: name, color: color, data: []};
      //Computing data iff possible:
      var wanted = $el.val();
      if(wanted !== '_'){
        var params = {};
        $inputs.each(function(){
          var $i = $(this);
          //Filtering wanted inputs:
          if($i.data('allowed').indexOf(wanted) < 0) return;
          //Name of this parameter:
          var pName = _.filter($i.attr('class').split(' '), function(s){
            return s !== 'reflectDistribution';
          }).join('');
          //Value of this parameter:
          params[pName] = parseInt($i.find('input').val(), 10);
        });
        console.log('DEBUG', params);
        // FIXME IMPLEMENT MAGIC TO HAPPEN HERE
        switch (wanted) {
          case 'U':

            break;
          case 'N':

            break;
          case 'L':

            break;
          case 'O':

            break;
        }
      }
      //Setting object in nameDistributionMap:
      nameDistributionMap[name] = distribution;
    };
    // Setting up events to gather distribution data:
    table.find('.distributionSelection').each(function(){
      var $el = $(this),
          $tr = $el.closest('tr'),
          $inputs = $tr.find('.reflectDistribution'),
          color = $tr.find('.hexColor input').val(), // [0-9a-fA-F]{6} | ^$
          name = $tr.find('.taxonsetName input').val();
      // Computation for different occasions:
      var computation = _.bind(computeDistribution, null, $el, $inputs, color, name);
      // Initial computation:
      computation();
      // Compute on selection change:
      $el.change(computation);
      // Compute on input change:
      $inputs.each(function(){
        $(this).change(computation);
      });
    });
  });
})();
