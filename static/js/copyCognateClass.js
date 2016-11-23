(function(){
  "use strict";
  return define(['jquery','lodash','bootbox'], function($, _, bootbox){
    /**
      In two language view this module searches for all occurences of
      `data-assigncognatesfromlexeme` to treat them as buttons that will assign
      a lexeme to a cognate class.
      The logic for this file shall also update the table in situ.
    */
    var $table = $('#viewTwoLanguages');
    if($table.length !== 1) return; // Guard that we have a $table.
    $table.find('[data-assigncognatesfromlexeme]').each(function(){
      var $btn = $(this);
      $btn.click(function(){
        var query = {
          'assigncognates': 'assigncognates',
          fromLexeme: $btn.data('assigncognatesfromlexeme'),
          toLexeme: $btn.data('assigncognatestolexeme'),
          'csrfmiddlewaretoken': $table.closest('form').find('[name="csrfmiddlewaretoken"]').val()
        };
        $.post('./', query).done(function(data){
          // data is expected to have fields ['idList', 'aliasList']
          var $tr = $btn.closest('tr'),
              $idCell = $tr.find('.cognateClassId'),
              $aliasCell = $tr.find('td .cognateClasses input');
          // Updating table:
          var mkCIdLink = function(cId){
            return '<a href="/cognate/'+cId+'/" ' +
                   'target="_blank" ' +
                   'style="color: #8B4510;"> '+cId+' </a>';
          };
          $idCell.html(_.map(data.idList, mkCIdLink).join(''));
          $aliasCell.val(data.aliasList.join(', '));
        }).fail(function(response){
          bootbox.alert(response.responseText);
        });
      });
    });
  });
})();
