$(window).ready(function(){
  reveal_driver_elem();
  demoUpload();
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

$("#profile_modal").on('show.bs.modal', function(){
  console.log('HERE');
  // demoUpload();
});

function demoUpload() {
  console.log('upload');
  var $uploadCrop;

  function readFile(input) {
    if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
        $('.upload-demo').addClass('ready');
              $uploadCrop.croppie('bind', {
                url: e.target.result
              }).then(function(){
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
    $uploadCrop.croppie('result', {
      type: 'base64'
    }).then(function (img) {
      $.post('/save_img', {img:img}, function(data, status){
        console.log(status);
      });
    });
  });
}
