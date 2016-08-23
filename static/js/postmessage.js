(function(){
  "use strict";
  return define([], function(){
    var listenerMap = {}; // Label -> (msg -> IO ())
    //Handle incomming messages:
    window.addEventListener("message", function(event){
      var recv = JSON.parse(event.data);
      if('label' in recv && 'msg' in recv){
        if(recv.label in listenerMap){
          listenerMap[recv.label](recv.msg);
        }
      }
    }, true);
    //Return module API:
    return {
      send: function(label, msg){
        window.postMessage(
          JSON.stringify({label: label, msg: msg}),
          window.location.origin);
      },
      listen: function(label, handler){
        if(typeof(handler) === 'function'){
          //Set or overwrite listener
          listenerMap[label] = handler;
        }else if(label in listenerMap){
          //Remove listener:
          delete listenerMap[label];
        }
      },
      getListener: function(label){
        return listenerMap[label];
      },
      listeners: function(){
        return Object.keys(listenerMap);
      }
    };
  });
}());
