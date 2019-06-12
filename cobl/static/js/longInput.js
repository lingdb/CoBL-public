(function(){
  "use strict";
  /**
    This module searches for text inputs that have a data-longinput="<int>".
    If the text of these inputs is >= than their value:
    * If the input doesn't have a tooltip, this module adds their value as tooltip.
    * If the user clicks on the input, and edit box modal will open.
    This functionality was requested in #385.
  */
  return define(['jquery','bootbox'], function($, bootbox){
    $('input[type="text"][data-longinput]').each(function(){
      var $this = $(this);
      var startLength = parseInt($this.data('longinput'), 10);

      if($this.val().length < startLength){
        return;
      }

      //Add tooltip if OK:
      if($this.data('toggle') !== 'tooltip'){
        $this.attr({
          "data-toggle": "tooltip",
          "data-placement": "top",
          "data-container": "body",
          "title": $this.val()
        }).tooltip();
      }

      //Handling click events:
      $this.click(function(){
        bootbox.prompt({
          title: "Edit cell contents:",
          inputType: 'textarea',
          value: $this.val(),
          callback: function(result){
              $this.val(result);
          }
        });
      });
    });
  });
})();
