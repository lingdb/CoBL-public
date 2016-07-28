(function(){
  "use strict";
  return define(['jquery', 'lodash',
                 'js/gatherCheckboxValues'],
                function($, _, gatherCheckboxValues){
    $('.editCognateClassButton').click(function(){
      //Gathering selected lexemes and their infos:
      var selected = gatherCheckboxValues('input.lexemeSelection');
      selected.push($(this).val());
      selected = _.map(selected, JSON.parse);
      //Deconstructing selected data:
      var lexemeIds = _.chain(selected).map(function(x){
        return x.lexemeId;
      }).uniq().value();
      var cognateClassIds = _.chain(selected).map(function(x){
        return x.cognateClassIds;
      }).flattenDeep().uniq().value();
      //Form to work with:
      var form = $('#addToCognateClassForm');
      //Cognate classes we know about:
      var cognateClassMap = {}; // id -> {id, alias, root_form, root_language}
      _.each(form.data('cognateclasses'), function(cc){
        cognateClassMap[cc.id] = cc;
      });
      //Building the name for a cognate class:
      var mkCognateClassName = function(cc, deli){
        deli = deli || ' , ';
        return _.filter([cc.alias,
                         cc.root_form,
                         cc.root_language], function(s){
                           return !_.isEmpty(s);
                         }).join(deli);
      };
      //Building options for a cognate class:
      var mkOptions = function(cId){
        return _.map(cognateClassMap, function(cc){
          var selected = (cc.id === cId) ? ' selected="selected"' : '';
          var name = mkCognateClassName(cc);
          return '<option value="'+cc.id+'"'+selected+'>'+name+'</option>';
        }).join('');
      };
      //Setting lexemeIds:
      form.find('input[name="lexemeIds"]').val(lexemeIds.join(','));
      //Providing editing for selected cognate classes:
      _.each(cognateClassIds, function(cId){
        //Current cognate class:
        var current = cognateClassMap[cId];
        //Composing cognate class name:
        var name = mkCognateClassName(current, '<br>');
        form.prepend(
          '<div class="form-group cognateClassSelection" ' +
               'data-for="'+current.id+'">' +
            '<label for="selectCognateClass"' +
                   'class="col-sm-3">' +
              name +
            '</label>' +
            '<div class="col-sm-9">' +
              '<select name="selectCognateClass">' +
                '<option value="new">New</option>' +
                '<option value="delete">Delete</option>' +
                mkOptions(current.id) +
              '</select>' +
            '</div>' +
          '</div>'
        );
      });
    });
  });
})();
