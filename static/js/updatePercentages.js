(function(){
  "use strict";
  return define(['jquery',
                 'lodash',
                 'js/viewTableFilter'],
                function($, _, viewTableFilter){
    /**
      How this module shall operate:
      1: Figure out if we've got a `.updatePercentages` element.
      2: Figure out if we've got a `.viewTableFilter`.
      3: Register callback for `.updateCounts`.
      4: Compute percentage whenever callback is called.
    */
    var module = {
      percentageTarget: '.updatePercentages',
      $percentageTarget: null,
      tableTarget: '.viewTableFilter',
    };
    module.init = function(){
      module.$percentageTarget = $(module.percentageTarget);
      if(module.$percentageTarget.length === 1 && $(module.tableTarget).length >= 1){
        viewTableFilter.callbacks.updatePercentages = module.updatePercentages;
        module.updatePercentages();
      }
    };
    module.updatePercentages = function(){
      //Calculate current average:
      var bars = $(module.tableTarget+' tbody tr:visible .progressBar .progress-bar');
      var barSum = 0;
      bars.each(function(){
        barSum += parseInt($(this).attr('aria-valuenow'));
      });
      module.presentAverage(barSum / bars.length);
    };
    module.presentAverage = function(average){
      var bar = module.$percentageTarget.find('.progress-bar');
      bar.attr('aria-valuenow', average);
      bar.css('width', average+'%');
      bar.find('span').text(average+'% Complete');
      //Adjust percentage classes:
      bar.removeClass(_.values(module.percentageClasses).join(' '));
      _.chain(_.keys(module.percentageClasses))
       .map(function(x){return parseInt(x);})
       .sortBy(_.identity)
       .find(function(limit){
          if(average <= limit){
            bar.addClass(module.percentageClasses[limit]);
            return true;
          }
          return false;
        }).value();
    };
    module.percentageClasses = {'25': 'progress-bar-danger',
                                '50': 'progress-bar-warning',
                                '75': 'progress-bar-info',
                                '100': 'progress-bar-success'};
    return module;
  });
}());
