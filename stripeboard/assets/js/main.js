$(document).ready(function (){
  var render, key, value;
  render = function (json) {
    // no data, try again in 5 seconds...
    if (json.paying_customers == 0) {
      return setTimeout(function() {
        $.getJSON(jsonUrl, render);
      }, 5000);
    };

    // replace on page variables
    for (key in json) {
      value = json[key];
      $('span[data-value-key="'+key+'"]').text(value);
    }

    // build data for graph
    var revenue = [];
    var customers = [];
    for (var i = 0; i < json.periods.length; i++) {
      period = json.periods[i];
      revenue.push({x: period.timestamp, y: period.monthly_revenue});
      customers.push({x: period.timestamp, y: period.customers});
    };

    // build graph
    var graph = new Rickshaw.Graph({
      element: document.querySelector('#chart'),
      width: 600,
      height: 575,
      renderer: 'line',
      series: [{
          name: 'Monthly Revenue',
          color: 'steelblue',
          data: revenue
        }, {
          name: 'Customers',
          color: 'slategrey',
          data: customers
      }]
    });

    graph.render();
    var hoverDetail = new Rickshaw.Graph.HoverDetail({
      graph: graph,
    });
  };

  $.getJSON(jsonUrl, render);
});