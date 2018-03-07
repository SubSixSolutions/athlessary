function reveal_driver_elem(){
  console.log('hello');
  num_seats = document.getElementById("num_seats").value;
  console.log(num_seats);

  if (num_seats > 0){
    $("#certify_driver").removeAttr("style");
    // $("#certify_driver").css('display:block;');
  }
  else {
    $("#certify_driver").attr("style", 'display:none;');
    // $("#certify_driver").css('display:none;');
  }
}
