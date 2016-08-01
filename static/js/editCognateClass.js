(function(){
  "use strict";
  return define(['jquery', 'lodash', 'bootbox',
                 'js/gatherCheckboxValues'],
                function($, _, bootbox, gatherCheckboxValues){
    $('.editCognateClassButton').click(function(){
      //Gathering selected lexemes and their infos:
      var selected = gatherCheckboxValues('input.lexemeSelection');
      selected.push($(this).val());
      selected = _.map(selected, JSON.parse);
      //Deconstructing selected data:
      var lexemeIds = _.chain(selected).map(function(x){
        return x.lexemeId;
      }).uniq().value();
      //Building a map from cognateClassIds to lexemeIds:
      var cognateClassLexemeMap = {}; // cId -> {lexemeId -> true}
      _.each(selected, function(x){
        _.each(x.cognateClassIds, function(cId){
          if(!(cId in cognateClassLexemeMap)){
            cognateClassLexemeMap[cId] = {};
          }
          cognateClassLexemeMap[cId][x.lexemeId] = true;
        });
      });
      //Array of cognateClassIds with only cIds that belong to all lexemes:
      var cognateClassIds = [];
      _.each(cognateClassLexemeMap, function(lObj, cId){
        if(_.keys(lObj).length === lexemeIds.length){
          cognateClassIds.push(cId);
        }
      });
      //Handling the modal:
      var handleForm = function(){
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
        //
        var mkCognateClassSelection = function(cId, name){
          return '<div class="form-group cognateClassSelection" ' +
               'data-for="'+cId+'">' +
            '<label for="selectCognateClass"' +
                   'class="col-sm-3">' +
              name +
            '</label>' +
            '<div class="col-sm-9">' +
              '<select name="selectCognateClass">' +
                '<option value="new">New</option>' +
                '<option value="delete">Delete</option>' +
                mkOptions(cId) +
              '</select>' +
            '</div>' +
          '</div>';
        };
        //Setting lexemeIds:
        form.find('input[name="lexemeIds"]').val(lexemeIds.join(','));
        //Removing old selections:
        form.find('.cognateClassSelection').remove();
        //Providing editing for selected cognate classes:
        _.each(cognateClassIds, function(cId){
          //Current cognate class:
          var current = cognateClassMap[cId];
          //Composing cognate class name:
          var name = mkCognateClassName(current, '<br>');
          form.prepend(mkCognateClassSelection(current.id, name));
        });
        //Handling the add button:
        form.find('#addEntryCognateClassButton').click(function(){
          var msg = 'Are you sure that you want to ' +
                    'add an additional cognate class?';
          bootbox.confirm(msg, function(result){
            if(result === true){
              form.prepend(mkCognateClassSelection('new', 'new'));
              //Making sure only one is added:
              form.find('#addEntryCognateClassButton').remove();
            }
          });
        });
        //Handling the save button:
        form.find('#editCognateClassButton').click(function(){
          //Gather cognate class assignments:
          var cognateClassAssignments = {};
          form.find('.cognateClassSelection').each(function(){
            var el = $(this);
            cognateClassAssignments[el.data('for')] =
              el.find('select[name="selectCognateClass"]').val();
          });
          form.find('input[name="cognateClassAssignments"]').val(
            JSON.stringify(cognateClassAssignments));
          //Submit the form:
          form.find('input[type="submit"]').trigger('click');
        });
        //Display modal:
        $('#editCognateClassModal').modal('show');
      };
      //Checking if we've got a nice selection:
      if(cognateClassIds.length === 0){
        var msg = 'The lexemes in your selection share ' +
                  'no common cognate class. ' +
                  'Are you sure you want to continue?';
        bootbox.confirm(msg, function(result){
          if(result === true){
            handleForm();
          }
        });
      }else{
        handleForm();
      }
    });
  });
})();
