(function(){
  "use strict";
  return define(['jquery','markdown-it'], function($, md){
    var module = {
      processor: new md(),
      /**
        @param target :: $
        Replaces text in target with rendered markdown html.
      */
      render: function(target){
        if(target instanceof $){
          var content = target.text();
          target.html(module.processor.render(content));
        }
      }
    };
    return module;
  });
})();
