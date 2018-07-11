(function(){
  "use strict";
  return define(['jquery'], function($){
    /**
      Mirrors the content of mirrorTextInput selected elements
      by where they have the same data-compare attribute.
    */
    var mirrorTextInput = '.mirrorTextInput';
    $(mirrorTextInput).each(function(){
      $(this).keyup(function(){
        var called  = this,
            $called = $(called),
            compare = $called.data('compare');
        $(mirrorTextInput).each(function(){
          if(this === called) return;
          var t = $(this);
          if(t.data('compare') === compare){
            t.val($called.val());
          }
        });
      });
    });
  });
})();
