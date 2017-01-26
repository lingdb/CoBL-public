(function(){
  "use strict";
  /* eslint-disable no-new */
  return define(['lodash', 'jquery', 'awesomplete'], function(_, $, Awesomplete){
    // parseDataTypeahead :: jQuery -> {} | []
    var parseDataTypeahead = function(input){
      /*
        Parsing the typeahead map requires unescaping unicode,
        which is inspired by [1].
        [1]: https://stackoverflow.com/a/7885499/448591
      */
      return $.parseJSON(input.data('typeahead').replace(
        /\\u([\d\w]{4})/gi,
        function(match, grp){
          return String.fromCharCode(parseInt(grp, 16));
      }));
    };
    // selectOnClick :: jQuery -> jQuery
    var selectOnClick = function(input){
      return input.click(function(){
        //https://stackoverflow.com/a/4067488/44859
        this.setSelectionRange(0, this.value.length);
      });
    };
    // mkOptions :: [string] -> {}
    var mkOptions = function(keys){
      return {
        list: keys,
        minChars: 1,
        autoFirst: true
      };
    };
    //Handling typeaheadText for prev_next templates:
    $('.typeaheadText').each(function(){
      var input = selectOnClick($(this));
      var data = parseDataTypeahead(input);
      new Awesomplete(input.get(0), mkOptions(_.keys(data)));
      //Handling selection event:
      input.on('awesomplete-selectcomplete', function(){
        var v = input.val();
        if(v in data){
          window.location = data[v];
        }
      });
    });
    //Handling typeaheadInput as used in lexeme_add.html:
    $('.typeaheadInput').each(function(){
      var input = selectOnClick($(this));
      var data = parseDataTypeahead(input);
      //Target input for this typeahead:
      var target = (function(){
        var tgt = 'input[name="'+input.data('inputfor')+'"]';
        return input.closest('form').find(tgt);
      })();
      //Init awesomplete:
      new Awesomplete(input.get(0), mkOptions(_.keys(data)));
      //Handling selection event:
      input.on('awesomplete-selectcomplete', function(){
        var v = input.val();
        if(v in data){
          target.val(data[v]);
        }
      });
      //Making sure input is valid:
      var pattern = '^'+_.keys(data).join('|')+'$';
      input.attr('pattern', pattern);
      //Setting the initial input if possible:
      var current = target.val();
      if(current !== ''){
        _.each(data, function(v, k){
          if(v == current){
            input.val(k);
            return false;
          }
        });
      }
    });
  });
})();
