(function(){
  "use strict";
  /**
    This module provides a function that computes distributions given some parameters.
  */
  return define(['lodash'], function(_){
    // Range for distributions:
    var distributionRange = {low: 0, high: 5000};
    /**
      o :: {name :: String,
            color :: String,
            params :: {String -> Float},
            type :: 'U' | 'N' | 'O' | 'L'}
      return distribution :: o ∧ {data :: [Float]}
    */
    return function(o){
      //Distribution object to compute:
      var distribution = _.extend(o, {data: []});
      if(_.isUndefined(o.params) || _.isUndefined(o.type)){
        return distribution;
      }
      var params = o.params;
      //Computing data iff possible:
      var x = 0, y = 0; // Variables used inside switch
      switch(o.type){
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
          for(x = distributionRange.low; x <= distributionRange.high; x+=10){
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
          for(x = distributionRange.low; x <= distributionRange.high; x+=10){
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
          for(x = distributionRange.low; x <= distributionRange.high; x+=10){
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
      return distribution;
    };
  });
}());
