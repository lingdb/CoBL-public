(function(){
  "use strict";
  return define(['jquery', 'lodash', 'js/apiRoutes'],
                function($, _, apiRoutes){
    var module = {
      $container: null
    };
    module.clear = function(){
      if(_.isNull(module.$container)){
        return;
      }
      module.$container.remove();
      module.$container = null;
    };
    module.display = function(content){
      $('body').append(
        '<div id="editCognateClassContent">' +
        content +
        '</div>');
      module.$container = $('#editCognateClassContent');
    };
    module.renderTable = function(data){
      // data :: [{id :: Int, alias :: String, placeholder :: String}]
      var rows = [];
      _.each(data, function(entry){
        rows.push(
          '<td>' +
          [entry.id,
           entry.alias,
           entry.placeholder].join('</td><td>') +
          '</td>');
      });
      return '<table class="table table-bordered">' +
             '<thead>' +
             '<th>Id</th>' +
             '<th>Alias</th>' +
             '<th>Placeholder</th>' +
             '</thead>' +
             '<tbody>' +
             '<tr>' + rows.join('</tr><tr>') + '</tr>' +
             '</tbody>' +
             '</table>';
    };
    module.fetchFor = function($input){
      var query = {lexemeid: $input.data('lexemeid')};
      $.getJSON(apiRoutes.cognatePlaceholders, query, function(data){
        console.log('Fetched something:', data);
        module.display(module.renderTable(data));
      });
    };
    module.init = function(){
      $('.combinedCognateClassAssignment').each(function(){
        var $this = $(this);
        $this.focus(function(){
          module.fetchFor($this);
        }).focusout(module.clear);
      });
    };
    return module;
  });
})();
