(function() {
  "use strict";
  return define(["jquery", "lodash", "bootstrap"], function($, _){
    var active = window.location.pathname.match(/^\/(sources)\//);
    if(active){
      var csrf_token = (function(cookies){
        cookies = cookies || "";
        var token = "";
        _.forEach(cookies.split(';'), function(cookie){
          var matches = cookie.match(/^.*csrftoken=(.+)$/);
          if(matches){
            token = matches[1];
            return false;
          }
        });
        return token;
      })(document.cookie);
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
      		var postdata = {
      			'postType': 'details',
      			'id': $(this).attr('id'),
      			'csrfmiddlewaretoken': csrf_token
      		};
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
      		var postdata = {
      			'postType': 'filter',
      			'filter_dict': filter_dict,
      			'csrfmiddlewaretoken': csrf_token
      		};
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
      		var postdata = {
      			'postType': 'add',
      			'csrfmiddlewaretoken': csrf_token
      		};
      		$.post("/sources/", postdata, function (data) {
      			build_edit_form(data, 'add');
      		});
      	});

      	/**** EDIT / DELETE *****/
      	$(document.body).on('click', '.edit_button.show_e', function() {
      		$('#editSourceContainer').empty();
      		$('#editSource').attr('source_id', $(this).attr('id'));
      		var postdata = {
      			'postType': 'edit',
      			'id': $(this).attr('id'),
      			'csrfmiddlewaretoken': csrf_token
      		};
      		$.post("/sources/", postdata, function (data) {
      			build_edit_form(data, 'edit');
      		});
      	});

      	/**** SUBMIT FORM *****/
      	$(document).on("click", ":submit", function(e){ // catch the form's submit event
      		//$('#editSource').submit(function() {
      		var postdata = {
            'postType': 'update',
      			'id':$('#editSource').attr('source_id'),
      			'csrfmiddlewaretoken': csrf_token,
      			'source_data': $(this).parent().serialize(),
      			'action': $(this).val()
          };
      		$.ajax({ // create an AJAX call...
      			data: postdata, // get the form data
      			type: $(this).parent().attr('method'), // GET or POST
      			url: $(this).parent().attr('action'), // the file to call
      			success: function(response) { // on success..
      				//$('#DIV_CONTAINING_FORM').html(response); // update the DIV
      			}
      		});
      		$('#editModal')[0].style.display = "none";
      		return false;
      	});

      	/**** CHANGE DEPRECATED STATUS *****/
      	$(document.body).on('click', 'input[name="deprecated"]', function() {
      		$(this).parent().parent().toggleClass('deprecated');
      		var postdata = {
      			'postType': 'deprecated-change',
      			'id': $(this).parent().siblings('.details').children().attr('id'),
      			'csrfmiddlewaretoken': csrf_token,
      			'status': $(this).is(':checked'),
      		};
      		$.post("/sources/", postdata, function(data){});
      	});

      	/**** CHANGE TRS STATUS *****/
      	$(document.body).on('click', 'input[name="TRS"]', function() {
      		$(this).parent().parent().toggleClass('TRS');
      		var postdata = {
      			'postType': 'TRS-change',
      			'id': $(this).parent().siblings('.details').children().attr('id'),
      			'csrfmiddlewaretoken': csrf_token,
      			'status': $(this).is(':checked'),
      		};
      		$.post("/sources/", postdata, function(data){});
      	});

      		/**** IMPORT *****/
      	$(document.body).on('click', 'button[id="import"]', function() {
      		window.location.replace('import/');
      	});
      }
    }
  });
})();
