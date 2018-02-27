function myFunction() {
  var input, filter, table, tr, td, i;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");
  var selected = document.querySelector("input[name=a]:checked").value;
  var search_col = 0;
  if (selected == 'Name'){
    search_col = 1;
  }
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[search_col];
    if (td) {
      if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

function reset_text(txt){
  $('#myInput').val('');
  $("#myInput").trigger("keyup");
  $('#myInput').attr("placeholder", 'Search ' + txt);
}

function create_date(utc_time, delimiter){
  var fullDate = new Date(0);
  fullDate.setUTCSeconds(utc_time);
  var twoDigitMonth = (fullDate.getMonth()+1)+"";
  if(twoDigitMonth.length==1){
    twoDigitMonth="0" +twoDigitMonth;
  }
  var twoDigitDate = fullDate.getDate()+"";
  if(twoDigitDate.length==1){
    twoDigitDate="0" +twoDigitDate;
  }
  return twoDigitMonth + delimiter + twoDigitDate + delimiter + fullDate.getFullYear();
}

function get_workout_by_id(_id, _url){
  $.post(_url,
      {workout_id: _id}, function (data, status) {
        $("#side_table > tbody").empty();

        var currentDate = create_date(data[0]['time'], "/");

        $("#cap").text(data[0]['name']);
        $("#_date").text(currentDate);

        for (var i = 0; i < data.length; i++) {
          var newRow = $("<tr>");
          var cols = "";

          var total_seconds = data[i]['seconds'] + (data[i]['minutes'] * 60);
          var splits = data[i]['distance'] / 500;
          var secs = ((total_seconds / splits) % 60).toFixed(2);
          var mins = (Math.trunc(total_seconds / splits / 60));

          if (data[i]['by_distance'] == 0){
            cols += '<td>' + data[i]['distance'] + '</td>';
          }
          else {
            cols += '<td>' + data[i]['minutes'] + ':' + data[i]['seconds'] + '</td>';
          }
          cols += '<td>' + mins + ':' + secs + '</td>';

          newRow.append(cols);
          $("#side_table").append(newRow);
        }
        if (data[0]['by_distance'] == 0){
          $("#head-1").text('Meters');
        }
        else {
          $("#head-1").text('Time');
        }
      });
}

function create_chart_object(){
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
                    // beginAtZero:true
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

  // populate the chart with data
  populate_chart('/api_hello', myChart);

  // set change workouts to be responsive
  elemm = document.getElementById('change_workout');
  elemm.onclick = function(){
    populate_chart('/api_hello', myChart);
  }
}

// function draw_chart(data) {
function draw_chart(data, myChart){
    //get data
    // data = get_workouts_by_name('/api_hello');
    // console.log(data);

    // unpack data dictionary
    var _data = data['data'];
    var _labels = data['labels'];
    var name = data['name'];
    var y_axis = data['y_axis'];
    var _ids = data['_ids'];
    console.log(_ids);
    console.log(data['_ids']);

    // set the data and labels of the chart
    myChart.data.datasets[0].data = _data;
    myChart.data.labels = _labels;

    // set onclick function with id array
    elemm = document.getElementById('myChart');
    elemm.onclick = function(evt) {
      var activePoints = myChart.getElementsAtEvent(evt);

      if (activePoints.length != 0){
        var index = activePoints[0]._index;
        get_workout_by_id(data['_ids'][index], '/get_a_workout');
      }
      // go(evt, '{{url_for('get_a_workout')}}', data['_ids']);
    };

    // update side table with the curr workouts
    get_workout_by_id(_ids[0], '/get_a_workout');

    // name the chart adn y-axis
    myChart.data.datasets[0].label = name;
    myChart.options.scales.yAxes[0].scaleLabel.labelString = y_axis;

    // reload the chart
    myChart.update();
}

// function get_workouts(_url) {
//     var elem = document.getElementById("workout");
//     var name = elem.options[elem.selectedIndex].text;
//     if (name == 'None'){
//         window.alert('Please add at least 2 workouts of the same kind!');
//         var data = {
//             'data': [],
//             'labels': [],
//             'y_axis': '---',
//             'name': 'Add Workouts!'
//         };
//         draw_chart(data);
//         return;
//     }
//     $.post(_url,
//         {share: name}, function (data, status) {
//             draw_chart(data);
//         }
//     );
//     return 0;
// }

function populate_chart(_url, chart_instance) {
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
        draw_chart(data, chart_instance);
    }
    $.post(_url,
        {share: name}, function (data, status) {
            console.log(data);
            draw_chart(data, chart_instance);
        }
    );
    return 0;
}

function get_date_and_time(utc_time){
  var fullDate = new Date(0);fullDate.setUTCSeconds(utc_time);
  var twoDigitMonth = (fullDate.getMonth()+1)+"";if(twoDigitMonth.length==1)	twoDigitMonth="0" +twoDigitMonth;
  var twoDigitDate = fullDate.getDate()+"";if(twoDigitDate.length==1)	twoDigitDate="0" +twoDigitDate;
  var currentDate = fullDate.getFullYear() + "-" + twoDigitMonth + "-" + twoDigitDate;
  var twoDigitHour = fullDate.getHours()+"";if(twoDigitHour.length==1)	twoDigitHour="0" +twoDigitHour;
  var twoDigitMin = fullDate.getMinutes()+"";if(twoDigitMin.length==1)	twoDigitMin="0" +twoDigitMin;
  var currentTime = twoDigitHour + ":" + twoDigitMin;
  return {
    date: currentDate,
    time: currentTime
  };
}

function modal_edit(_id, _url){
  var a_model = document.getElementById('a_modal');
  if (a_model){
    $.post(_url,
        {workout_id: _id}, function (data, status) {

          $("#modal_table > thead").empty();
          $("#modal_table > tbody").empty();

          for (var i = 0; i < data.length; i++) {
            var newRow = $("<tr>");
            var cols = "";

            date_cell = '<input type=text ></input>'

            cols += '<td>' + (i+1) + '</td>';

            if (data[i]['by_distance'] == 0){
              cols += '<td><input type=\"number\" name=\"meters' + data[i]['erg_id'] + '\" value=\'' + data[i]['distance'] + '\'></td>';
            }
            else {
              cols += '<td><input type=number name=\"minutes' + data[i]['erg_id'] + '\" value=\'' + data[i]['minutes'] + '\'></td>';
              cols += '<td><input type=number name=\"seconds' + data[i]['erg_id'] + '\" value=\'' + data[i]['seconds'] + '\'></td>';
            }

            newRow.append(cols);
            $("#modal_table > tbody").append(newRow);
          }
          $("#modal_table > thead").append('<th>' + 'Piece' + '</th>');

          var date_time =  get_date_and_time(data[0]['time']);

          $("#time").val(date_time['time']);
          $("#date").val(date_time['date']);
          $("#m_header > h5").text(data[0]['name']);

          if (data[0]['by_distance'] == 0){
            $("#modal_table > thead").append('<th>' + 'Meters' + '</th>');
          }
          else {
            $("#modal_table > thead").append('<th>' + 'Minutes' + '</th>');
            $("#modal_table > thead").append('<th>' + 'Seconds' + '</th>');
          }
    });
    $('#a_modal').modal('show');
    elemm = document.getElementById('save_changes');
    elemm.onclick = function() { edit_a_workout(_id); };
  }
}

function edit_a_workout(_id){
  $.post('/get_a_workout',
      {workout_id: _id}, function (data, status) {
        console.log(data);
        var form_data = $('#edit_form').serializeArray().reduce(function(obj, item) {
            obj[item.name] = item.value;
            return obj;
        }, {});

        var orig_date_time = get_date_and_time(data[0]['time']);
        var orig_time = orig_date_time['time'];
        var orig_date = orig_date_time['date'];

        var _ids = [];
        var meters = [];
        var mins = [];
        var secs = [];
        var by_dist = 0;
        var new_date = form_data['date'];
        var old_date = data[0]['time'];
        var w_id = data[0]['workout_id'];
        var time = form_data['time'];

        // meters
        if (data[0]['by_distance'] == 0){
          for (var i = 0; i < data.length; i++){
            var curr_meter_name = 'meters' + data[i]['erg_id'];
            if (curr_meter_name in form_data){
              curr_meter = form_data[curr_meter_name];
              if (curr_meter != data[i]['distance']){
                meters.push(curr_meter);
                _ids.push(data[i]['erg_id']);
              }
            }
          }
          by_dist = 1;
        }
        // minutes and seconds
        else {
          for (var i = 0; i < data.length; i++){
            var curr_min_name = 'minutes' + data[i]['erg_id'];
            var curr_sec_name = 'seconds' + data[i]['erg_id']
            if (curr_min_name in form_data && curr_sec_name in form_data){
              curr_min = form_data[curr_min_name];
              curr_sec = form_data[curr_sec_name];
              if (curr_min != data[i]['minutes'] || curr_sec != data[i]['seconds']){
                mins.push(curr_min);
                secs.push(curr_sec);
                _ids.push(data[i]['erg_id']);
              }
            }
          }
          by_dist = 0;
        }
        if (_ids.length > 0 || new_date != orig_date || time != orig_time){
          $.post('/edit_workout',
              {   minutes: mins,
                  seconds: secs,
                  by_distance: by_dist,
                  erg_ids: _ids,
                  meters: meters,
                  new_date: new_date,
                  old_date: old_date,
                  workout_id: w_id,
                  time: time,
              }, function (data, status) {
                window.location.reload();
          });
        }
  });
}


$(window).ready(function(){
  create_chart_object();
});
