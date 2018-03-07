$(window).ready(function(){
  console.log('begin');
  populate_roster();
});

function populate_roster(){
  $.get('/get_all_athletes', function (data, status){
    console.log(data);
    for (var i = 0; i < data.length; i++){
      var newRow = $("<tr>");
      var cols = "";

      cols += '<td class=\"align-middle\">' + data[i]['first'] + '</td>';
      cols += '<td class=\"align-middle\">' + data[i]['address'] + '</td>';
      cols += '<td class=\"align-middle\">' + data[i]['num_seats'] + '</td>';
      cols += '<td class=\"text-center\"><input type=\"radio\"></td>';
      cols += '<td class=\"text-center\"><input class=\"\" type=\"radio\"></td>';

      newRow.append(cols);
      $("#athlete_table > tbody").append(newRow);
    }
  });
}
