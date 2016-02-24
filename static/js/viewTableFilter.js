(function(){
  "use strict";
  return define(['jquery','lodash'], function($, _){
    /*
      This view can be used to filter and sort tables.
      The table is expected to contain input elements
      that may have one of the inputClasses.
      The table may also contain .btn elements that may have one of the btnClasses.
      Both the inputs and the .btn elements shall have data-selector attributes
      that select the elements to sort/filter by relative to each tr in the tbody.
    */
    var module = {
      inputClasses: ['filterText', 'filterInput', 'filterSwadesh',
                     'filterCognate', 'filterBool'],
      btnClasses: ['sortInput','sortText','sortIntText']
    };
    /**
      Function to initialize viewTableFilter:
      @param el :: $ | window.Element | selector string
    */
    module.init = function(el){
      //Sanitize el:
      if(el instanceof window.Element || _.isString(el)){
        el = $(el);
      }
      //Actual init work:
      el.each(function(){
        var table = $(this);
        //Attaching inputClasses:
        _.each(module.inputClasses, function(inputClass){
          if(inputClass in module){
            table.find('input.'+inputClass).each(function(){
              var input = $(this);
              input.change(function(){
                module[inputClass](input, table);
              });
            });
            table.find('button.'+inputClass).each(function(){
              var button = $(this);
              button.click(function(){
                module[inputClass](button, table);
              });
            });
          }else{
            console.log('inputClass not implemented:', inputClass);
          }
        });
        //Attaching btnClasses:
        _.each(module.btnClasses, function(btnClass){
          if(btnClass in module){
            table.find('.btn.'+btnClass).each(function(){
              var btn = $(this);
              btn.click(function(){
                module[btnClass](btn, table);
              });
            });
          }else{
            console.log('btnClass not implemented:', btnClass);
          }
        });
      });
    };
    /**
      @param table    :: $ ∧ table
      @param reverse  :: Bool
      @param iteratee :: ($ ∧ row) -> *
      General sort method, private to this module.
    */
    var sortBy = function(table, reverse, iteratee){
      //Rows to sort:
      var rows = [];
      table.find('tbody > tr').each(function(){
        rows.push($(this));
      });
      //Sorting:
      var sorted = _.sortBy(rows, iteratee);
      return reverse ? _.reverse(sorted) : sorted;
    };
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      @return reverse :: Bool
    */
    var updateSortButtons = function(btn, table){
      var reverse = (btn.find('.glyphicon-sort-by-attributes').length !== 0);
      //Set .btn icons:
      _.each(module.btnClasses, function(btnClass){
        table.find('.btn.'+btnClass).each(function(){
          $(this).html('<span class="glyphicon glyphicon-sort"></span>');
        });
      });
      //Set own icon:
      if(reverse){
        btn.html('<span class="glyphicon glyphicon-sort-by-attributes-alt"></span>');
      }else{
        btn.html('<span class="glyphicon glyphicon-sort-by-attributes"></span>');
      }
      //Done:
      return reverse;
    };
    /**
      @param λ :: selector string -> ($ ∧ row) -> *
      @return func :: ($ ∧ .btn, $ ∧ table) -> *
      This function is a factory for sort* functions
      that takes a predicate as parameter.
    */
    var sortTableBy = function(λ){
      return function(btn, table){
        var reverse = updateSortButtons(btn, table);
        var iteratee = λ(btn.data('selector'));
        var rows = sortBy(table, reverse, iteratee);
        _.each(rows, function(row){
          table.append(row);
        });
      };
    };
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by text in a column
    */
    module.sortText = sortTableBy(function(selector){
      return function(row){
        return row.find(selector).text().trim();
      };
    });
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by text parsed as int in a column
    */
    module.sortIntText = sortTableBy(function(selector){
      return function(row){
        return parseInt(row.find(selector).text().trim(), 10);
      };
    });
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by text parsed as int in a column
    */
    module.sortInput = sortTableBy(function(selector){
      return function(row){
        return row.find(selector).val();
      };
    });
    //Finished module:
    return module;
  });
})();
