(function(){
  "use strict";
  return define(['jquery',
                 'lodash',
                 'js/viewTableFilter'],
                function($, _, viewTableFilter){
    /**
      How this module shall operate:
      1: Figure out if we've got a .updateCounts element.
      2: Figure out if we've got a .viewTableFilter.
      3: Register callbacks for the .updateCounts
      4: Compute counts whenever callbacks are called.
    */
    var module = {
      countTarget: '.updateCounts',
      $countTarget: null, //Filled by init
      tableTarget: '.viewTableFilter',
      initial: 0, // Initial value of $countTarget
      separator: ' / '
    };
    module.init = function(){
      module.$countTarget = $(module.countTarget);
      if(module.$countTarget.length === 1 && $(module.tableTarget).length >= 1){
        module.initial = module.$countTarget.text();
        //Setting callback and initial execution of updateCounts:
        viewTableFilter.callbacks.updateCounts = module.updateCounts;
        module.updateCounts();
      }
    };
    module.updateCounts = function(){
      var counts = _.map(module.$countTarget.data('countformat').split(' '),
                         function(task){
        if(task in module){
          task = module[task];
          if(_.isFunction(task)){
            return task.call(module);
          }else{
            return task;
          }
        }
      }, this);
      module.$countTarget.text(counts.join(module.separator));
    };
    module.countVisible = function(){
      var count = $(module.tableTarget + ' tbody>tr:visible').length;
      return count;
    };
    return module;
  });
}());
