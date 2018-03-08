$(window).ready(function(){
  reveal_driver_elem();
});

function reveal_driver_elem(){
  num_seats = document.getElementById("num_seats").value;
  console.log(num_seats);

  if (num_seats > 0){
    $("#certify_driver").removeAttr("style");
  }
  else {
    $("#certify_driver").attr("style", 'display:none;');
  }
}
