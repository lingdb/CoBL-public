(function(){
  "use strict";
  /* eslint-disable no-console */
  /*eslint max-depth: ["error", 8]*/
  return define(['jquery','lodash',
                 'js/cladeFilter',
                 'js/viewTableFilter/settings',
                 'js/viewTableFilter/phoneticData',
                 'floatThead', 'bootstrap'],
    function($, _, mkCladeFilter, settings, phoneticData){
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
                     'filterBool', 'filterDistinct',
                     'filterNumber', 'filterNumberInput',
                     'filterPhonetic', 'filterPhoneticInput'],
      btnClasses: ['sortInput', 'sortIntInput', 'sortText', 'sortIntText'],
      callbacks: {} // :: Identifier -> IO ()
    };
    /**
      Making sure resetting of filter settings is possible
      independently of init:
    */
    $('#viewTableFilterReset').click(settings.cleanStorage);
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
      var floatOptions = {position: 'absolute'};
      if(el.data('floatheadtop')){
        floatOptions.top = parseInt(el.data('floatheadtop'), 10);
      }
      el.floatThead(floatOptions);
      //Actual init work:
      el.each(function(){
        var table = $(this);
        // try to place thead fixed based on wrapped element
        table.floatThead({
            scrollContainer: function(table){
                return table.closest('.wrapper');
            }
        });
        //Fix overflow for #356:
        if(this.offsetWidth < this.scrollWidth){
          var ttd = table.find('td');
          for(var i=0; i<ttd.length; i+=1){
            var e = ttd[i];
            //https://stackoverflow.com/a/10017343/448591
            e.tooltip({
              title: e.text(),
              placement: 'top',
              container: 'body',
              trigger: 'hover'
            });
          }
        }
        //Restoring buttons before initial filtering.
        settings.restoreButtonInputs();
        //Attaching inputClasses:
        _.each(module.inputClasses, function(inputClass){
          $('input.'+inputClass).each(function(){
            var $input = $(this);
            $input.keyup(function(){
              module[inputClass]($input, table);
              settings.storeKeyupInput($input, inputClass);
              markNewMeanings();
            });
          });
          var btnClasses = $('button.'+inputClass);
          var numOfClasses = btnClasses.length;
          var cnt = 0;
          btnClasses.each(function(){
            var $button = $(this);
            cnt += 1;
            $button.click(function(){
              module[inputClass]($button, table);
              settings.storeButtonInput($button, inputClass);
              markNewMeanings();
            });
            //Initial filtering for the last element of a given class:
            module[inputClass]($button, table, true, (cnt == numOfClasses));
          });
        });
        //Attaching btnClasses:
        _.each(module.btnClasses, function(btnClass){
          table.find('.btn.'+btnClass).each(function(){
            var $btn = $(this);
            $btn.click(function(){
              module[btnClass]($btn, table);
              settings.storeSortInput($btn, btnClass);
              markNewMeanings();
            });
          });
        });
        settings.restoreSortInput(module);
        //cladeFilter:
        var λ = _.bind(filter, null, table);
        var cladeFilter = mkCladeFilter(λ);
        if(cladeFilter){
          filterPredicates.cladeFilter = cladeFilter;
          λ();
        }
        //Mark group of meanings if desired via class 'markNewMeanings'
        markNewMeanings();
      });
      //Load previous settings:
      settings.restoreKeyupInputs();
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
    module.updateSortButtons = function(btn, table){
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
        var reverse = module.updateSortButtons(btn, table);
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
      Function to sort rows of a table by text in a column.
    */
    module.sortText = sortTableBy(function(selector){
      return function(row){
        return row.find(selector).text().trim();
      };
    });
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by text parsed as int in a column.
    */
    module.sortIntText = sortTableBy(function(selector){
      return function(row){
        return parseFloat(row.find(selector).text().trim());
      };
    });
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by lowercase text from an input in a column.
    */
    module.sortInput = sortTableBy(function(selector){
      return function(row){
        return row.find(selector).val().toLowerCase();
      };
    });
    /**
      @param btn   :: $ ∧ .btn
      @param table :: $ ∧ table
      Function to sort rows of a table by input value parsed as int in a column.
    */
    module.sortIntInput = sortTableBy(function(selector){
      return function(row){
        return parseFloat(row.find(selector).val());
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
      Filtering triggers module.callbacks.
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
      //Trigger callbacks:
      _.each(module.callbacks, function(λ){
        λ.call(this);
      }, this);
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
          var re;
          var inval = input.val();
          inval = inval.trim();
          if(inval.startsWith('@')){ // first char @ -> case sensitive
            inval = inval.replace('@', '');
            try{
              re = new RegExp(inval, "");
              filterPredicates[id] = mkPredicate(selector, re);
            }catch(e){re = null;}
          }else{
            try{
              re = new RegExp(inval, "i");
              filterPredicates[id] = mkPredicate(selector, re);
            }catch(e){re = null;}
          }
        }
        filter(table);
      };
    };
    /**
      @param prefix :: string
      @param mkPredicate :: (selector string, RegExp) -> $ ∧ row -> Bool
    */
    var mkSimpleFilter = function(prefix, mkPredicate){
      return function(input, table){
        var selector = input.data('selector');
        var id = prefix+selector;
        if(input.val() === ''){
          delete filterPredicates[id];
        }else{
          filterPredicates[id] = mkPredicate(selector, input.val());
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
        var $input = row.find(selector);
        if($input){
          var text = $input.val().trim();
          return text.match(re) === null;
        }
        return true;
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
      var wanted;
      if(initial !== true){
        if(btn.hasClass('btn-danger')){
          wanted = null; // remove -> question
        }else if(btn.hasClass('btn-success')){
          wanted = false; // ok -> remove
        }else if(btn.hasClass('btn-default')){
          wanted = true; // question -> ok
        }
      }else{
        if(btn.hasClass('btn-danger')){
          wanted = false; // remove -> remove
        }else if(btn.hasClass('btn-success')){
          wanted = true; // ok -> ok
        }else if(btn.hasClass('btn-default')){
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
      markNewMeanings
      If table has class 'markNewMeaning' the change from one meaning to
      a new one will be marked via adding class 'startNewMeaning'
    */
    var markNewMeanings = function(){
      var table = $('.markNewMeaning');
      var markNewMeanings = true;
      if(typeof table === "undefined"){markNewMeanings = false;}
      if(markNewMeanings){
        var curKey = "";
        var ttr = table.find('tbody > tr');
        for(var i=0; i<ttr.length; i+=1){
          var e = $(ttr[i]);
          e.removeClass('startNewMeaning');
          if(!e.hasClass('hide')){
            var cText = e.data('meaningid');
            if(cText !== curKey){
              e.addClass('startNewMeaning');
              curKey = cText;
            }
          }
        }
      }
    };
    /**
      @param input :: $ ∧ button.filterBool
      @param table :: $ ∧ table
      @param initial :: Bool
      If initial is set filterBool shall not change the buttons content.
    */
    module.filterBool = function(btn, table, initial, last){
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
      //Filtering - while initializing only for last element
      //   of a given inputClass to avoid multiple filtering
      if(!initial || (initial && last)){
        filter(table);
      }
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
        var idCountMapTargetLg = {};
        var idCountMapSourceLg = {};
        var getRowId = function(row){return row.data(dataAttr);};
        if(table.attr('id') === 'viewTwoLanguages'){
          table.find('tbody > tr').each(function(){
            var row = $(this);
            if(!row.hasClass('hide')){
              var rId = getRowId(row);
              if(row.data('issourcelg')){
                if(rId in idCountMapTargetLg){
                  idCountMap[rId] = 1;
                }else{
                  idCountMapSourceLg[rId] = 1;
                }
              }else{
                if(rId in idCountMapSourceLg){
                  idCountMap[rId] = 1;
                }else{
                  idCountMapTargetLg[rId] = 1;
                }
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
            return ((idCountMap[rId]==1) !== wanted);
          };
        }else{
          idCountMap = {};
          getRowId = function(row){return row.data(dataAttr);};
          var ttr = table.find('tbody > tr');
          for(var k=0; k<ttr.length; k+=1){
            var row = $(ttr[k]);
            if(row.is(':visible')){
              var rId = getRowId(row);
              if(rId in idCountMap){
                idCountMap[rId] += 1;
              }else{
                idCountMap[rId] = 1;
              }
            }
          }
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
      }
      //Filtering
      filter(table);
    };
    /**
      mkNumberFilter :: (re :: String) -> (text :: String) -> Bool
    */
    var mkNumberPredicate = function(filterVal){
      filterVal = filterVal.trim().replace(/[^\d.\-=<>]*/g, '');
      console.log(filterVal);
      var match = filterVal.match(/^(\d+?)\-(\d+)$/);
      if(match){
        var number1 = parseFloat(match[1], 10);
        var number2 = parseFloat(match[2], 10);
        return function(t){return parseFloat(t, 10) < number1 || parseFloat(t, 10) > number2;};
      }else{
        filterVal = filterVal.trim().replace(/\-/g, '');
        match = filterVal.match(/^([<>]?=?)(\-?[\d.]+)$/);
        if(match){
          var number = parseFloat(match[2], 10);
          switch (match[1]) {
            case '>':
              return function(t){return parseFloat(t, 10) <= number;};
            case '<':
              return function(t){return parseFloat(t, 10) >= number;};
            case '>=':
              return function(t){return parseFloat(t, 10) < number;};
            case '<=':
              return function(t){return parseFloat(t, 10) > number;};
            case '=':
            /* falls through */
            default:
              return function(t){return parseFloat(t, 10) !== number;};
          }
        }
        console.log('Invalid filter string:', filterVal);
        return function(){return false;};
      }
    };
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterNumber = mkSimpleFilter('filterText', function(selector, filterVal){
      var predicate = mkNumberPredicate(filterVal);
      return function(row){
        return predicate(row.find(selector).text());
      };
    });
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterNumberInput = mkSimpleFilter('filterInput', function(selector, filterVal){
      var predicate = mkNumberPredicate(filterVal);
      return function(row){
        var $input = row.find(selector);
        return $input ? predicate($input.val()) : true;
      };
    });
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterPhonetic = mkSimpleFilter('filterText', function(selector, filterVal){
      return function(row){
        return phoneticData.matches(filterVal, row.find(selector).text());
      };
    });
    /**
      @param input :: $ ∧ input.filterText
      @param table :: $ ∧ table
    */
    module.filterPhoneticInput = mkSimpleFilter('filterInput', function(selector, filterVal){
      return function(row){
        var $input = row.find(selector);
        return $input ? phoneticData.matches(filterVal, $input.val()) : true;
      };
    });
    //Finished module:
    return module;
  });
})();
