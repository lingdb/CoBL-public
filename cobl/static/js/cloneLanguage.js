(function(){
  "use strict";
  return define(['jquery'], function($){
    var modal = $('#cloneLanguageModal');
    if(modal.length === 1){
      $('button[data-toggle="cloneLanguageModal"]').each(function(){
        var btn = $(this).click(function(){
          var srcName = btn.data('sourcelanguagename');
          var languageId = btn.data('languageid');
          modal.find('.sourceLanguageName').val(srcName);
          modal.find('.languageId').val(languageId);
          modal.modal({show: true});
        });
      });
    }
  });
})();
