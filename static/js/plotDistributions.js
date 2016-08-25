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
  return define(['jquery','lodash','c3','js/postmessage'], function($, _, c3, msg){
    if($('#distributionPlot').length !== 1) return;
    /**
      Map from taxonsetName to distribution calculated via computeDistribution.
      nameDistributionMap :: String -> {name :: String,
                                        color :: String,
                                        data :: [Int]}
    */
    var nameDistributionMap = {};
    var chart = c3.generate({
        axis: {
          x: {
            tick: {
              count: 11,
              format: function(x){return x*10;}
            }
          }
        },
        bindto: '#distributionPlot .chart',
        data: {
          columns: [],
          color: function(c, d){
            var wanted = c;
            if(d.id && d.id in nameDistributionMap){
              wanted = '#' + nameDistributionMap[d.id].color;
            }
            if(wanted != c){
              var delta = {};
              delta[d.id] = wanted;
              chart.data.colors(_.extend(chart.data.colors(), delta));
            }
            return wanted;
          }
        },
        transition: {
          duration: 0
        },
        interaction: {
          enabled: false
        },
        point: {
          show: false
        }
    });
    //Listen to distribution updates:
    msg.listen('distribution', function(distribution){
      nameDistributionMap[distribution.name] = distribution;
      if(distribution.data.length > 0){
        console.log('Updating distribution:', distribution.name);
        chart.load({
          columns: [
            _.concat([distribution.name], distribution.data)
          ]
        });
      }else{
        chart.unload({
          ids: distribution.name
        });
      }
    });
    //Initial request for all distributions:
    msg.send('distribution.initial', 'all');
  });
})();
