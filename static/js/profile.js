// Declare global chart
var ctx = $('#myChart');
var myChart = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: [{
      backgroundColor: [
          'rgba(176,196,222, 0.2)',
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
          'rgba(153, 102, 255, 0.2)',
          'rgba(255, 159, 64, 0.2)'
      ],
      borderColor: [
          'rgba(176,196,222, 1)',
          'rgba(255,99,132,1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)'
      ],
      borderWidth: 1
    }]
  },
  options: {
      scales: {
          yAxes: [{
              ticks: {
                  beginAtZero:true
              },
              scaleLabel: {
                  display: true,
                  labelString: 'y_axis'
              }
          }],
          xAxes: [{
              scaleLabel: {
                  display: true,
                  labelString: 'Date'
              }
          }]
      }
  }
});


function draw_chart(data) {
    var _data = data['data'];
    var _labels = data['labels'];
    var name = data['name'];
    var y_axis = data['y_axis'];

    myChart.data.datasets[0].data = _data;
    myChart.data.datasets[0].label = name;
    myChart.data.labels = _labels;

    myChart.options.scales.yAxes[0].scaleLabel.labelString = y_axis;

    myChart.update();
}

function get_workouts(_url) {
    var elem = document.getElementById("workout");
    var name = elem.options[elem.selectedIndex].text;
    if (name == 'None'){
        window.alert('Please add at least 2 workouts of the same kind!');
        var data = {
            'data': [],
            'labels': [],
            'y_axis': '---',
            'name': 'Add Workouts!'
        };
        draw_chart(data);
        return;
    }
    console.log(name);
    $.post(_url,
        {share: name}, function (data, status) {
            console.log(data['data']);
            console.log(status);
            draw_chart(data);
        }
    );
}

function get_meters_rowed(_url){
  var elem = document.getElementById("meters_rowed");
  $.get(_url, function(data, status) {
    console.log(data['total_meters']);
    elem.innerHTML = data['total_meters'];
  });
}
