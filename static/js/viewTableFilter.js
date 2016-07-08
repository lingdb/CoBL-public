(function(){
  "use strict";
  return define(['jquery','lodash',
                 'js/cladeFilter',
                 'floatThead'],
    function($, _, mkCladeFilter){
    /*
      This view can be used to filter and sort tables.
      The table is expected to contain input elements
      that may have one of the inputClasses.
      The table may also contain .btn elements that may have one of the btnClasses.
      Both the inputs and the .btn elements shall have data-selector attributes
      that select the elements to sort/filter by relative to each tr in the tbody.
    */
    var module = {
      inputClasses: ['filterText', 'filterInput',
                     'filterBool', 'filterDistinct'],
      btnClasses: ['sortInput', 'sortText', 'sortIntText']
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
      //floatThead for #31:
      el.floatThead({position: 'absolute'});
      //Actual init work:
      el.each(function(){
        var table = $(this);
        //Attaching inputClasses:
        _.each(module.inputClasses, function(inputClass){
          if(inputClass in module){
            $('input.'+inputClass).each(function(){
              var input = $(this);
              input.keyup(function(){
                module[inputClass](input, table);
              });
            });
            $('button.'+inputClass).each(function(){
              var button = $(this);
              button.click(function(){
                module[inputClass](button, table);
              });
              //Initial filtering for buttons:
              module[inputClass](button, table, true);
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
        //cladeFilter:
        var λ = _.bind(filter, null, table);
        var cladeFilter = mkCladeFilter(λ);
        if(cladeFilter){
          filterPredicates.cladeFilter = cladeFilter;
          λ();
        }
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
        return parseFloat(row.find(selector).text().trim());
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
    /**
      The filterPredicates :: id string -> ($ ∧ row) -> Bool
      is used to filter rows using all selectors.
      Predicates shall return True if something needs to be hidden.
    */
    var filterPredicates = {};
    /**
      @param table :: $ ∧ table
      The general filter function
      used by the modules specialised filter functions.
    */
    var filter = function(table){
      table.find('tbody > tr').each(function(){
        var row = $(this);
        var hide = _.some(filterPredicates, function(λ){
          return λ(row);
        });
        if(hide){
          row.addClass('hide');
        }else{
          row.removeClass('hide');
        }
      });
    };
    /**
      @param prefix :: string
      @param mkPredicate :: (selector string, RegExp) -> $ ∧ row -> Bool
    */
    var mkStringFilter = function(prefix, mkPredicate){
      return function(input, table){
        var selector = input.data('selector');
        var id = prefix+selector;
        if(input.val() === ''){
          delete filterPredicates[id];
        }else{
          var re = new RegExp(input.val(), "i");
          filterPredicates[id] = mkPredicate(selector, re);
        }
        filter(table);
      };
    };
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterText = mkStringFilter('filterText', function(selector, re){
      return function(row){
        var text = row.find(selector).text().trim();
        return text.match(re) === null;
      };
    });
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterInput = mkStringFilter('filterInput', function(selector, re){
      return function(row){
        var text = row.find(selector).val().trim();
        return text.match(re) === null;
      };
    });
    /**
      Helper function for module.{filterBool,filterDistinct}
      @param btn :: $
      @param initial :: Bool
      @return wanted :: Bool
      This function checks the given button to infer `wanted` from it.
      If initial is not set, the button will be changed to the next state.
    */
    var filterBoolButtton = function(btn, initial){
      var span = btn.find('.glyphicon');
      var wanted;
      if(initial !== true){
        if(span.hasClass('glyphicon-remove-sign')){
          wanted = null; // remove -> question
        }else if(span.hasClass('glyphicon-ok-sign')){
          wanted = false; // ok -> remove
        }else if(span.hasClass('glyphicon-question-sign')){
          wanted = true; // question -> ok
        }
      }else{
        if(span.hasClass('glyphicon-remove-sign')){
          wanted = false; // remove -> remove
        }else if(span.hasClass('glyphicon-ok-sign')){
          wanted = true; // ok -> ok
        }else if(span.hasClass('glyphicon-question-sign')){
          wanted = null; // question -> question
        }
      }
      //Adjust button if not initial:
      if(initial !== true){
        if(wanted === null){
          // remove -> question
          btn.removeClass('btn-danger').addClass('btn-default')
             .html('<span class="glyphicon glyphicon-question-sign"></span>');
        }else if(wanted){
          // question -> ok
          btn.removeClass('btn-default').addClass('btn-success')
             .html('<span class="glyphicon glyphicon-ok-sign"></span>');
        }else{
          // ok -> remove
          btn.removeClass('btn-success').addClass('btn-danger')
             .html('<span class="glyphicon glyphicon-remove-sign"></span>');
        }
      }
      return wanted;
    };
    /**
      @param input :: $ ∧ button.filterBool
      @param table :: $ ∧ table
      @param initial :: Bool
      If initial is set filterBool shall not change the buttons content.
    */
    module.filterBool = function(btn, table, initial){
      //Find wanted kind of filter:
      var wanted = filterBoolButtton(btn, initial);
      //Un-/Registering filter function:
      var selector = btn.data('selector');
      var id = 'filterBool'+selector;
      if(wanted === null){
        delete filterPredicates[id];
      }else{
        filterPredicates[id] = function(row){
          var checked = row.find(selector).prop('checked');
          return checked !== wanted;
        };
      }
      //Filtering
      filter(table);
    };
    /**
      @param input :: $ ∧ button.filterBool
      @param table :: $ ∧ table
      @param initial :: Bool
      If initial is set filterDistinct shall not change the buttons content.
    */
    module.filterDistinct = function(btn, table, initial){
      //Find wanted kind of filter:
      var wanted = filterBoolButtton(btn, initial);
      //Un-/Registering filter function:
      var dataAttr = btn.data('attr');
      var id = 'filterDistinct'+dataAttr;
      if(wanted === null){
        delete filterPredicates[id];
      }else{
        var idCountMap = {};
        var getRowId = function(row){return row.data(dataAttr);};
        table.find('tbody > tr').each(function(){
          var row = $(this);
          if(row.is(':visible')){
            var rId = getRowId(row);
            if(rId in idCountMap){
              idCountMap[rId] += 1;
            }else{
              idCountMap[rId] = 1;
            }
          }
        });
        /*
          We implement wanted as:
          true -> Only display lexemes where the same meaning was found twice.
          false -> Only display lexemes where the meaning was found just once.
        */
        filterPredicates[id] = function(row){
          var rId = getRowId(row);
          return ((idCountMap[rId] > 1) !== wanted);
        };
      }
      //Filtering
      filter(table);
    };
    //Finished module:
    return module;
  });
})();
