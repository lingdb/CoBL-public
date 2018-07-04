(function() {
  "use strict";
  return define(["jquery", "lodash", "js/csrfToken", "bootstrap"], function($, _, csrfToken){
    var active = window.location.pathname.match(/^\/(sources)\//);
    if(active){
      var permitted = $('.permissionDiv').data('permitted') || false;
      $(document).ready(function() {
        /* Enable tooltips */
        $('[data-toggle="tooltip"]').tooltip();

        function format_table() {
          $('input:checked[name="deprecated"]').parent().parent().toggleClass('deprecated');
          $('input:checked[name="TRS"]').parent().parent().toggleClass('TRS');
          if(!permitted){
            $('th.deprecated, td.deprecated').hide();
            $('th.TRS, td.TRS').hide();
            $('th.edit, td.edit').hide();
            $('button#import').hide();
            $('button#add').hide();
            $('.filter-header th').slice(-3).hide();
          }
        }
        format_table();

        /**** DETAILS *****/
        $(document.body).on('click', '.details_button.show_d', function() {
          $(this).toggleClass('show_d hide_d');
          $(this).text('Hide');
          var row = $(this).parent().parent();
          row.addClass('highlighted');
          var postdata = _.extend({
            'postType': 'details',
            'id': $(this).attr('id')
          }, csrfToken);
          $.post("/sources/", postdata, function (data) {
            var details_table = $('<tr><td colspan="12"><table class="details_table"/></td></tr>').insertAfter(row);
            $(data).children('th').appendTo(details_table.find('table.details_table')).wrapAll('<thead class="_details"/>');
            $(data).children('td').appendTo(details_table.find('table.details_table')).wrapAll('<tbody><tr class="_details"/></tbody>');
            details_table.find('input, textarea').each(function() {
              $(this).parent('td').attr('class', $(this).attr('class'));
              $(this).replaceWith("<p>" + this.value + "</p>");
            });
          });
          return false;
        }).on('click', '.hide_d', function() {
          $(this).parent().parent().removeClass('highlighted');
          $(this).parent().parent().next().remove();
          $(this).toggleClass('show_d hide_d');
          $(this).text('More');
          return false;
        });

        /**** EXPORT *****/
        $(document.body).on('click', 'button[id="export"]', function() {
          window.location.replace('export/');
        });

        /**** FILTER TABLE *****/
        var delay = (function(){
          var timer = 0;
          return function(callback, ms){
          clearTimeout (timer);
          timer = setTimeout(callback, ms);
         };
        })();

        $('.filter-column input').keyup(function() {
          delay(function(){
          filter_table();
          }, 1000 );
        });

        function filter_table(){
          var filter_dict = {};
          $(".filter-column").each(function(){
            var key = $(this).attr('id').toLowerCase();
            var value = $(this).children('input').val();
            filter_dict[key] = value;
          });
          filter_dict = [JSON.stringify(filter_dict)];
          var postdata = _.extend({
            'postType': 'filter',
            'filter_dict': filter_dict
          }, csrfToken);
          $.post("/sources/", postdata, function (data) {
            var $data = $( data );
            $('tbody').replaceWith($data.find('tbody'));
            $('ul.pagination').replaceWith($data.find('ul.pagination'));
            format_table();
          });
        }
      });

      if(permitted){
        /**** EDIT / ADD / DELETE FORM *****/
        var build_edit_form = function(data, type){
          $('#editSourceContainer').append('<table id="edit_modal"/>');
            $('#editSource input').css({'display':'none'});
            $('#editSource input.'+type).css({'display':'initial'});
            $('#edit_modal').append($(data));
            $('<thead/>').appendTo($('#edit_modal'));
            $('<tbody/>').appendTo($('#edit_modal'));
            $('#edit_modal').find('tr').each(function (i) {
              $(this).children('th').appendTo($('#edit_modal').find('thead:last-of-type'));
              $(this).children('td').appendTo($('#edit_modal').find('tbody:last-of-type'));
              $(this).remove();
              if((i+1) % 4 === 0){
                $('<thead/>').appendTo($('#edit_modal'));
                $('<tbody/>').appendTo($('#edit_modal'));
              }
            });
          $('#editModal')[0].style.display = "block";
          return false;
        };

        $(document.body).on('click', '.close', function() {
          $('#editModal')[0].style.display = "none";
          return false;
        });

        /**** ADD *****/
        $(document.body).on('click', 'button[id="add"]', function() {
          $('#editSourceContainer').empty();
          var postdata = _.extend({'postType': 'add'}, csrfToken);
          $.post("/sources/", postdata, function (data) {
            build_edit_form(data, 'add');
          });
        });

        /**** EDIT / DELETE *****/
        $(document.body).on('click', '.edit_button.show_e', function() {
          $('#editSourceContainer').empty();
          $('#editSource').attr('source_id', $(this).attr('id'));
          var postdata = _.extend({
            'postType': 'edit',
            'id': $(this).attr('id')
          }, csrfToken);
          $.post("/sources/", postdata, function (data) {
            build_edit_form(data, 'edit');
          });
        });

        /**** SUBMIT FORM *****/
        $(document).on("click", ":submit", function(){ // catch the form's submit event
          //$('#editSource').submit(function() {
          var postdata = _.extend({
            'postType': 'update',
            'id':$('#editSource').attr('source_id'),
            'source_data': $(this).parent().serialize(),
            'action': $(this).val()
          }, csrfToken);
          $.ajax({
            data: postdata,
            type: $(this).parent().attr('method'),
            url: $(this).parent().attr('action'),
            success: function() {
              //$('#DIV_CONTAINING_FORM').html(response);
            }
          });
          $('#editModal')[0].style.display = "none";
          return false;
        });

        /**** CHANGE DEPRECATED STATUS *****/
        $(document.body).on('click', 'input[name="deprecated"]', function() {
          $(this).parent().parent().toggleClass('deprecated');
          var postdata = _.extend({
            'postType': 'deprecated-change',
            'id': $(this).parent().siblings('.details').children().attr('id'),
            'status': $(this).is(':checked'),
          }, csrfToken);
          $.post("/sources/", postdata, function(){});
        });

        /**** CHANGE TRS STATUS *****/
        $(document.body).on('click', 'input[name="TRS"]', function() {
          $(this).parent().parent().toggleClass('TRS');
          var postdata = _.extend({
            'postType': 'TRS-change',
            'id': $(this).parent().siblings('.details').children().attr('id'),
            'status': $(this).is(':checked'),
          }, csrfToken);
          $.post("/sources/", postdata, function(){});
        });

          /**** IMPORT *****/
        $(document.body).on('click', 'button[id="import"]', function() {
          window.location.replace('import/');
        });
      }
    }
  });
})();
