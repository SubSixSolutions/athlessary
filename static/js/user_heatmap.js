var heatmap;
var oldWidth;

function display_past_three_workouts(){
  $.get('/get_past_three_workouts', function(data, status){
    console.log(data);

    var workouts = document.createElement('div');
    workouts.className = 'row';
    for (i = 0; i < data.length; i++){
      var workout = document.createElement('div');
      workout.className = 'row shadow-sm mb-2 mb-lg-2 rounded';
      workout.innerHTML += "<div class=\"col-12\"><h5 class=\"text-center\">" + data[i]['name'] + " - " + (new Date(data[i]['time']).toDateString()) + "</h5></div>";
      workout.innerHTML += "<div class=\"col-12\"><p class=\"text-center\">" + data[i]['avg_min'] + ":" + data[i]['avg_sec'] + "</p></div>"

      document.getElementById('recent_workouts').appendChild(workout);
    }

  });
}

function create_heat_map(){
  // get data from database
  $.get('/generate_individual_heatmap', function(data, status){

    // make date field into a javascript date object
    data.forEach(function(element) {
      element['date'] = new Date(element['date']);
    });

    // call set up heatmap
    heatmap = calendarHeatmap()
      .data(data)
      .selector('#my-spot')
      .tooltipEnabled(true)
      .colorRange(['#DCDCDC', '#ff8c00'])
      .onClick(function (data) {
        console.log('data', data);
      });
    heatmap();  // render the chart
  });
}

$(document).ready(function () {
    var oldWidth = $(window).width();

    // resize profile image
    resize_profile_picture();
});

$(window).resize(function () {
   if ($(window).width() != oldWidth) {
      // update the size of the current browser (oldWidth)
         oldWidth = $(window).width();
         heatmap();
   }
   resize_profile_picture();
});
