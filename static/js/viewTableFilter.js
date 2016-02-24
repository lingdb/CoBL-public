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
      inputClasses: ['filterText', 'filterInput', 'filterSwadesh'],
      btnClasses: ['sortInput','sortCheck','sortText','sortIntText']
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
        console.log('Hello viewTableFilter!');
        var table = $(this);
        //Attaching inputClasses:
        _.each(module.inputClasses, function(inputClass){
          if(inputClass in module){
            table.find('input.'+inputClasses).each(function(){
              var input = $(this);
              input.change(function(){
                module[inputClass](input);
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
                module[btnClass](btn);
              });
            });
          }else{
            console.log('btnClass not implemented:', btnClass);
          }
        });
      });
    };
    return module;
  });
})();
