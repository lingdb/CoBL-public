(function(){
  "use strict";
  return define(['jquery','lodash'], function($, _){
    var modal = $('#cloneLanguageModal');
    if(modal.length === 1){
      $('button[data-toggle="cloneLanguageModal"]').each(function(){
        var btn = $(this).click(function(){
          var srcName = btn.data('sourcelanguagename');
          modal.find('.sourceLanguageName').val(srcName);
          modal.modal({show: true});
        });
      });
    }
  });
})();
