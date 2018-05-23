var heatmap;
var oldWidth;

function generate_heatmap(chartData){
    var oldWidth = $(window).width();

    heatmap = calendarHeatmap()
      .data(chartData)
      .selector('#my-spot')
      .tooltipEnabled(true)
      .colorRange(['#DCDCDC', '#ff8c00'])
      .onClick(function (data) {
        console.log('data', data);
      });
    heatmap();  // render the chart
};

$(window).resize(function () {
   if ($(window).width() != oldWidth) {
      // update the size of the current browser (oldWidth)
         oldWidth = $(window).width();
         heatmap();
   }
});
