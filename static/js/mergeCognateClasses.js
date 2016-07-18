(function(){
  "use strict";
  return define(['jquery', 'bootbox',
                 'js/gatherCheckboxValues'],
                function($, bootbox, gatherCheckboxValues){
    var button = $('#mergeCognateClasses');
    if(button.length === 1){
      button.click(function(){
        var mergeIds = gatherCheckboxValues('input.mergeCognateClasses');
        if(mergeIds.length <= 1){
          bootbox.alert('Please select at least 2 entries to merge first.');
        }else{
          var msg = "Are you sure you want to merge the selected cognate classes?";
          bootbox.confirm(msg, function(result){
            if(result === true){
              var form = $('#mergeCognateClassesForm');
              form.append('<input name="mergeIds" value="'+mergeIds.join(',')+'">');
              form.find('input[type="submit"]').trigger('click');
            }
          });
        }
      });
    }
  });
})();
