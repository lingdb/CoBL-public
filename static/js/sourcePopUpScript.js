(function() {
  "use strict";
  return define(["jquery", "bootbox", "lodash", "django-dynamic-formset"], function($, bootbox, _){
    var active = window.location.pathname.match(/^\/(cognateclasslist|meaning)\//);
    if(active){
      $(document).ready(function() {
        var mkRow = function(entry){
          var idInput = entry.id ? '<input class="hide" type="text" data-key="id" value="' + entry.id + '">' : '';
          var select = '<select data-autocomplete-light-function="select2" data-autocomplete-light-url="/source-autocomplete/" data-key="source_id">' +
              '<option value="">---------</option>' +
              '<option value="' + entry.source_id + '" selected="selected">' + entry.source_name + '</option>' +
            '</select>';
          return '<tr data-id="' + entry.id + '">' +
            '<td>' + select + '</td>' +
            '<td><input class="form-control" style="width: 3em;" type="text" data-key="pages" value="' + entry.pages + '"></td>' +
            '<td><textarea data-key="comment">' + entry.comment + '</textarea></td>' +
            '<td><a class="btn btn-xs removeRow">remove</a>' + idInput + '</td>' +
            '</tr>';
        };

        var mkTable = function(entries){
          return '<table class="table table-bordered">' +
            "<thead><tr>" +
              "<th>Source</th>" +
              "<th>Pages</th>" +
              "<th>Comment</th>" +
              "<th>Delete</th>" +
              "</tr></thead><tbody>" +
              _.map(entries, mkRow).join('') +
            "</tbody></table>";
        };

        var removeHandler = function(){
          $(this).closest('tr').remove();
        };

        var build_cit_form = function(data) {
          var modal = bootbox.dialog({
            title: 'Edit sources',
            message: mkTable(data.entries) +
              '<a class="btn btn-info addRow">Add row</a>' +
              '<a class="btn btn-primary saveTable">Submit</a>'
          });
          modal.find('.removeRow').click(removeHandler);
          modal.find('.addRow').click(function(){
            modal.find('table tbody').append(mkRow({
              'source_name': '', pages: '', comment: ''}));
            modal.find('table tbody tr:last .removeRow').click(removeHandler);
          });
          modal.find('.saveTable').click(function(){
            var entries = [];
            modal.find('tbody tr').each(function(){
              var entry = {};
              $(this).find('[data-key]').each(function(){
                var $this = $(this);
                entry[$this.data('key')] = $this.val();
              });
              entries.push(entry);
            });
            var query = {
               postType: 'update',
               csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
               source_data: entries,
               action: 'Submit',
               id: data.id,
               model: data.model,
            };
            $.post("/cognateclasslist/", query, function(data){
              //FIXME IMPLEMENT
              /*
                var id = response.id;
                var model = response.model;
                var badgeUpdate = response.badgeUpdate;
                $('.openModal[id="' + id + '"][model="' + model + '"]').text(badgeUpdate);
              */
            });
          });
        };
        $('.openModal').click(function(){
          var $this = $(this);
          var query = {
            'postType': 'viewCit',
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            'id': $this.data('id'),
            'model': $this.data('model')
          };
          $.post("/cognateclasslist/", query, build_cit_form);
        });
      });
    }
  });
})();
