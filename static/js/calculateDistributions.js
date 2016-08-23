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
    // Range for distributions:
    var distributionRange = {low: 0, high: 5000};
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
        /**
        Params will have keys ∈ {
          logNormalOffset, logNormalMean, logNormalStDev,
          normalMean, normalStDev,
          uniformUpper, uniformLower}
        */
        var params = {};
        $inputs.each(function(){
          var $i = $(this);
          //Filtering wanted inputs:
          if($i.data('allowed').indexOf(wanted) < 0){
            msg.send('distribution', distribution);
            return;
          }
          //Name of this parameter:
          var pName = _.filter($i.attr('class').split(' '), function(s){
            return s !== 'reflectDistribution';
          }).join('');
          //Value of this parameter:
          var val = parseFloat($i.find('input').val(), 10);
          if(_.isNaN(val)){
            msg.send('distribution', distribution);
            return;
          }
          params[pName] = val;
        });
        // General range will be [0, 10,000] years BP.
        var x = 0, y = 0; // Variables used inside switch
        switch(wanted){
          case 'U':
            /*
              f(x)
               | x ∈ [a,b] = 1/(b-a)
               | otherwise = 0
              See https://en.wikipedia.org/wiki/Uniform_distribution_(continuous)
            */
            //Computing y = 1/(b-a):
            y = 1/(params.uniformUpper - params.uniformLower);
            //Filling distribution.data:
            for(x = distributionRange.low; x <= distributionRange.high; x++){
              var onInterval = (x >= params.uniformLower && x <= params.uniformUpper);
              distribution.data.push(onInterval ? y : 0);
            }
            break;
          case 'N':
            /*
              Normal distribution defined as follows:
              f(x | µ,σ) = e^(-(x-μ)^2/(2 σ^2))/(sqrt(2 π) σ)
              µ is the mean, σ is the standard deviation
              See https://en.wikipedia.org/wiki/Normal_distribution
                  http://www.wolframalpha.com/input/?i=normal+distribution
            */
            for(x = distributionRange.low; x <= distributionRange.high; x++){
              y = Math.pow(Math.E, -(Math.pow(x - params.normalMean, 2)/(2 * Math.pow(params.normalStDev, 2)))) / (Math.sqrt(2 * Math.PI) * params.normalStDev);
              distribution.data.push(y);
            }
            break;
          case 'L':
            /*
              Log-Normal distribution defined as follows:
              N_l(x | µ,σ) = (1/xσ√(2π)) e^(-((ln(x)-µ)²/(2σ²)))
              piecewise | e^(-(log(x)-μ)^2/(2 σ^2))/(sqrt(2 π) σ x) | x>0
                      0 | (otherwise)
              See https://en.wikipedia.org/wiki/Log-normal_distribution
                  http://www.wolframalpha.com/input/?i=log+normal+distribution
            */
            params.logNormalOffset = 0;
            /* falls through */
          case 'O':
            /*
              * Because we want to put in years as our mean directly,
                we take the ln(logNormalMean) as our µ.
              * To apply the offset we take x - offset which shifts the graph into the positive x.
            */
            var ssqtp = params.logNormalStDev * Math.sqrt(2 * Math.PI); // σ√(2π)
            var tss = 2 * Math.pow(params.logNormalStDev, 2); // 2σ²
            for(x = distributionRange.low; x <= distributionRange.high; x++){
              var xi = x - params.logNormalOffset;
              if(xi > 0){
                y = Math.pow(Math.E, -(Math.pow(Math.log(xi) - Math.log(params.logNormalMean), 2)/(2 * Math.pow(params.logNormalStDev, 2)))) / (Math.sqrt(2 * Math.PI) * params.logNormalStDev * xi);
                distribution.data.push(y);
              }else{
                distribution.data.push(0);
              }
            }
            break;
        }
        //Add distribution to chart:
        msg.send('distribution', distribution);
        console.log('DEBUG', distribution.name, distribution.data);
      }
    };
    // Setting up events to gather distribution data:
    table.find('.distributionSelection').each(function(){
      var $el = $(this),
          $tr = $el.closest('tr'),
          $inputs = $tr.find('.reflectDistribution'),
          color = $tr.find('.hexColor input').val(), // [0-9a-fA-F]{6} | ^$
          name = $tr.find('.taxonsetName input').val();
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
