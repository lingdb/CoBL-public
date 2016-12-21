(function() {
  "use strict";
  return define(["jquery", "django-dynamic-formset"], function($) {
    var active = window.location.pathname.match(/^\/(cognateclasslist|meaning)\//);
    if(active){
      $(document).ready(function() {
        /***** BUILD CITATIONS FORM *****/
        function build_cit_form(data) {

          $('#viewCitContainer').append(data);
          var formTemplate = $('#formTemplateContainer tr');
          formTemplate.find('input:hidden[id $= "-DELETE"]').remove();
          // Clear all cloned fields, except those the user wants to keep
          formTemplate.find('input,select,textarea,label,div').each(function() {
            var elem = $(this);
            if (elem.is('input:checkbox') || elem.is('input:radio')) {
              elem.attr('checked', false);
              // consider forking django-dynamic-templates and adding this fix to clear autocomplete forms
            } else if (elem.is('select[data-autocomplete-light-function="select2"]')) {
              elem.parent().html('<select data-autocomplete-light-function="select2" data-autocomplete-light-url="/source-autocomplete/" id="id_citations-0-source" name="citations-0-source"/>');
            } else {
              elem.val('');
            }
          });
          $('#citations tbody tr').formset({
            prefix: 'citations',
            formTemplate: formTemplate,
          });
          $('#viewCitContainer form tr:last .delete-row').trigger("click");
          $('#viewCit')[0].style.display = "block";
          return false;
        }

        /***** VIEW CITATIONS *****/
        $(document.body).on('click', '.openModal', function() {
          $(this).toggleClass('selected');
          $('#viewCitContainer').empty();
          var postdata = {
            'postType': 'viewCit',
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            'id': $(this).attr('id'),
            'model': $(this).attr('model'),
          };
          $.post("/cognateclasslist/", postdata, function(data) {
            build_cit_form(data);
          });
          return false;
        });

        /**** CLOSE CITATIONS VIEW *****/
        $(document.body).on('click', '.close', function() {
          close_modal();
          return false;
        });

        function close_modal() {
          $('.openModal.selected').removeClass('selected');
          $('#viewCit')[0].style.display = "none";
        }

        /***** SUBMIT FORM *****/
        $(document).on("click", "#viewCitContainer :submit", function(e) { // catch the form's submit event
          var postdata = {
            'postType': 'update',
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            'source_data': $('form#citations').serialize(),
            'action': $(this).val(),
            'id': $('.openModal.selected').attr('id'),
            'model': $('.openModal.selected').attr('model'),
          };
          $.ajax({ // create an AJAX call...
            data: postdata, // get the form data
            type: $(this).parent().attr('method'), // GET or POST
            url: $(this).parent().attr('action'), // the file to call
            success: function(response) { // on success..
              var id = response.id;
              var model = response.model;
              var badgeUpdate = response.badgeUpdate;
              $('.openModal[id="' + id + '"][model="' + model + '"]').text(badgeUpdate);
            }
          });
          close_modal();
          return false;
        });
      });
    }
  });
})();
