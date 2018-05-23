function resize_profile_picture(){
  div_width = $("#img_row").width();
  if (div_width <= 250) {
    $("#profile_img").height(div_width);
    $("#profile_img").width(div_width);
  }
  else {
    $("#profile_img").height(250);
    $("#profile_img").width(250);
  }
}
