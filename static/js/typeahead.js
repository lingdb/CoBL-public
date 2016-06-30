(function(){
  "use strict";
  return define(['lodash', 'jquery', 'awesomplete'], function(_, $, Awesomplete){
    $('.typeaheadText').each(function(){
      var input = $(this).click(function(){
        //https://stackoverflow.com/a/4067488/44859
        this.setSelectionRange(0, this.value.length);
      });
      /*
        Parsing the typeahead map requires unescaping unicode,
        which is inspired by [1].
        [1]: https://stackoverflow.com/a/7885499/448591
      */
      var data = $.parseJSON(input.data('typeahead').replace(
        /\\u([\d\w]{4})/gi,
        function(match, grp){
          return String.fromCharCode(parseInt(grp, 16));
      }));
      //Initializing Awesomplete:
      var awesomplete = new Awesomplete(input.get(0), {
        list: _.keys(data),
        minChars: 1,
        autoFirst: true
      });
      //Handling selection event:
      input.on('awesomplete-selectcomplete', function(){
        var v = input.val();
        if(v in data){
          window.location = data[v];
        }
      });
    });
  });
})();
