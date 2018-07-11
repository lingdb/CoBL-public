(function(){
  "use strict";
  return define(["lodash"], function(_){
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
    return {'csrfmiddlewaretoken': csrf_token};
  });
})();
