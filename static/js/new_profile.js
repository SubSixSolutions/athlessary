$(window).ready(function(){
  reveal_driver_elem();
  demoUpload();
});

$(document).ready(function(){
  $(window).resize(function(e){
    console.log(e);
    console.log($("#profile_img").width());
    div_width = $("#img_row").width();
    if (div_width <= 250) {
      $("#profile_img").height(div_width);
      $("#profile_img").width(div_width);
    }
    else {
      $("#profile_img").height(250);
      $("#profile_img").width(250);
    }
  }).resize();
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

function demoUpload() {
  console.log('upload');
  var $uploadCrop;

  function readFile(input) {
    if (input.files && input.files[0]) {
      var reader = new FileReader();

      reader.onload = function (e) {
        $('.upload-demo').addClass('ready');
        $uploadCrop.croppie('bind', {
          url: e.target.result }).then(function(){
                  console.log('jQuery bind complete');
          });
      }

      reader.readAsDataURL(input.files[0]);
      $("#save_profile_img").removeClass('disabled');
    }
    else {
          swal("Sorry - you're browser doesn't support the FileReader API");
    }
  }

  $uploadCrop = $('#upload-demo').croppie({
    viewport: {
      width: 200,
      height: 200,
      type: 'square'
    },
    enableExif: true
  });

  $('#upload').on('change', function () { readFile(this); });
  $('#save_profile_img').on('click', function (ev) {
    if (!$('#save_profile_img').hasClass('disabled')){
      $uploadCrop.croppie('result', {
        type: 'base64',
        size: { width: 300, height: 300 }
      }).then(function (img) {
        $.post('/save_img', {img:img}, function(data, status){
          console.log(status);
          $("#profile_img").src = data['img'];
        });
      });
    }
  });
}