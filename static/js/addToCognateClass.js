(function(){
  "use strict";
  return define(['jquery', 'bootbox',
                 'js/gatherCheckboxValues'],
                function($, bootbox, gatherCheckboxValues){
    var button = $('#addToCognateClassButton');
    if(button.length === 1){
      button.click(function(){
        var selected = gatherCheckboxValues('input.lexemeSelection');
        if(selected.length < 1){
          bootbox.alert('Please select at least 1 entry ' +
                        'to add to a cognate set.');
        }else{
          var form = $('#addToCognateClassForm');
          form.append('<input name="lexemeIds" class="hide" value="'+selected.join(',')+'">');
          form.find('input[type="submit"]').trigger('click');
        }
      });
    }
  });
})();
