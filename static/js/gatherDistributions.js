(function(){
  "use strict";
  /**
    See if there is a table.distributionPlot on the site,
    and perform the necessary setup.

    This code shall follow a loose FRP principle.
    For each row:
    * We check the distribution, both initially and on change.
    * We gather the distribution data so that it's ready to plot:
      - initially
      - On distribution change
      - On change of any value
    * We plot the distribution(s) in a (special) div using c3.
  */
  return define(['jquery','lodash','js/postmessage'], function($, _, msg){
    var table = $('table.distributionPlot');
    if(table.length !== 1) return;
    /**
      Map from taxonsetName to distribution calculated via computeDistribution.
      nameDistributionMap :: String -> {name :: String,
                                        color :: String,
                                        data :: [Int]}
    */
    var nameDistributionMap = {};
    //Chart to work with:
    var chart = null; // Initialized towards the end.
    /**
    Function to compute distribution data.
      $el :: $('select'), expected length === 1
      $inputs :: $('tr.reflectDistribution')
      color :: string
      name :: string
    */
    var computeDistribution = function($el, $inputs, color, name){
      //Distribution object to compute:
      var distribution = {name: name, color: color, data: []};
      //Setting object in nameDistributionMap:
      nameDistributionMap[name] = distribution;
      //Computing data iff possible:
      var wanted = $el.val();
      if(wanted !== '_'){
        distribution.type = wanted;
        /**
        Params will have keys ∈ {
          logNormalOffset, logNormalMean, logNormalStDev,
          normalMean, normalStDev,
          uniformUpper, uniformLower}
        */
        var params = {}, paramsOk = true;
        $inputs.each(function(){
          var $i = $(this);
          //Filtering wanted inputs:
          if($i.data('allowed').indexOf(wanted) < 0){
            return;
          }
          //Name of this parameter:
          var pName = _.filter($i.attr('class').split(' '), function(s){
            return s !== 'reflectDistribution';
          }).join('');
          //Value of this parameter:
          var val = parseFloat($i.find('input').val(), 10);
          if(!_.isNaN(val)){
            params[pName] = val;
          }else{
            paramsOk = false;
          }
        });
        if(paramsOk){
          distribution.params = params;
        }
      }
      //Add distribution to chart:
      msg.send('distribution', distribution);
    };
    // Setting up events to gather distribution data:
    table.find('.distributionSelection').each(function(){
      var $el = $(this),
          $tr = $el.closest('tr'),
          $inputs = $tr.find('.reflectDistribution'),
          color = $tr.find('.hexColor input').val(), // [0-9a-fA-F]{6} | ^$
          name = $tr.find('.taxonsetName input').val();
      //In case of language table color or name may behave differently:
      if(_.isUndefined(color)){
        color = $tr.find('.languageBranchColor').css('background-color');
        //color needs conversion to hex:
        //Inspired by https://stackoverflow.com/a/30381663/448591
        color = color.replace("rgba", "")
                     .replace("rgb", "")
                     .replace("(", "")
                     .replace(")", "");
        color = color.split(","); // get Array["R","G","B"]
        color = ('0' + parseInt(color[0], 10).toString(16)).slice(-2) +
                ('0' + parseInt(color[1], 10).toString(16)).slice(-2) +
                ('0' + parseInt(color[2], 10).toString(16)).slice(-2);
      }
      if(_.isUndefined(name)){
        name = $tr.find('.languageName input.language_name').val();
      }
      // Computation for different occasions:
      var computation = _.bind(computeDistribution, null, $el, $inputs, color, name);
      // Initial computation:
      computation();
      // Compute on selection change:
      $el.change(computation);
      // Compute on input change:
      $inputs.each(function(){
        $(this).change(computation);
      });
    });
    //Waiting for request to send initial distributions
    msg.listen('distribution.initial', function(req){
      if(req === 'all'){
        _.each(nameDistributionMap, _.bind(msg.send, null, 'distribution'));
      }
    });
  });
})();
