(function(){
  "use strict";
  return define(['lodash','jquery','bootbox'], function(_, $, bootbox){
    $('.bootboxHtmlSnippet[data-htmlsource]').click(function(){
      var source = $(this).data('htmlsource');
      $.get(source).fail(function(){
        console.error('Failed to fetch source.', arguments);
        bootbox.alert('Sorry, the server did not answer as expected.');
      }).done(function(data){
        bootbox.dialog({
          message: data,
          title: 'The server says:',
          buttons: {
            close: {
              label: 'Close',
              classname: 'btn-default'
            }
          }
        });
      });
    });
  });
})();
