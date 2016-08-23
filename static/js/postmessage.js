(function(){
  "use strict";
  return define(['intercom'], function(intercom){
    if(!intercom) intercom = window.Intercom;
    var spaceport = intercom.getInstance();
    //Making sure we clean up afterwards:
    window.addEventListener("beforeunload", function(e){
      intercom.destroy();
    }, false);
    //Return module API:
    return {
      send: function(label, msg){
        spaceport.emit(label, msg);
      },
      listen: function(label, handler){
        spaceport.on(label, handler);
      }
    };
  });
}());
