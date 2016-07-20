(function(){
  "use strict";
  return define(['jquery', 'bootbox',
                 'js/gatherCheckboxValues'],
                function($, bootbox, gatherCheckboxValues){
    var button = $('#createCognateClass');
    if(button.length === 1){
      button.click(function(){
        var selected = gatherCheckboxValues('input.lexemeSelection');
        if(selected.length <= 1){
          bootbox.alert('Please select at least 2 entries ' +
                        'to create a new cognate set for.');
        }else{
          var msg = "Are you sure that you want to create " +
                    "a new cognate class with the selected entries?";
          bootbox.confirm(msg, function(result){
            if(result === true){
              var form = $('#createCognateClassForm');
              form.append('<input name="lexemeIds" value="'+selected.join(',')+'">');
              form.find('input[type="submit"]').trigger('click');
            }
          });
        }
      });
    }
  });
})();
