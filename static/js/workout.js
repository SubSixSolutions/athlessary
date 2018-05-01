$(window).ready(function () {
    demoUpload();
});

$(document).ready(function(){
  $("#add_workout_form").on('submit', function(e){
    e.preventDefault();
    var _url = $(this).attr('action');

    var meters = []; var minutes = []; var seconds = []; var by_distance = "";
    var arr = $(this).serializeArray()
    $.each(arr, function(obj, item) {
        console.log(item.name);
        if (item.name == 'meters'){
          meters.push(item.value);
        }
        else if (item.name == 'minutes') {
          minutes.push(item.value);
        }
        else if (item.name == 'seconds'){
          seconds.push(item.value);
        }
    });
    by_distance = document.getElementById("units").value;
    console.log(document.getElementById("add_workout_form").elements);
    var elements = document.getElementById("add_workout_form").elements;
    var post = validate_workout_form(elements);

    if (post == false){
      return false;
    }
    console.log(meters, minutes, seconds, by_distance);
    $.post(_url, {
      workout_type: by_distance,
      meters: meters,
      minutes: minutes,
      seconds: seconds
    }, function(data, status){
      console.log(status);
      reset_form();
      var workout_name = data['name'];
      if (status == 'success'){
        var alert_div = document.createElement('div');
        alert_div.className = "alert alert-success alert-dismissible fade show mt-2";
        alert_div.role = "alert";
        alert_div.innerHTML =
                "<strong>Success!</strong> Workout " + workout_name + " Saved." +
                "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Close\">" +
                    "<span aria-hidden=\"true\">&times;</span>"
                "</button>"
        $("#info-div").append(alert_div)
      }
    });
  });
});


function switch_input(){
  var input = document.getElementById('second_input_div');
  is_visible = input.hidden;
  var min_meter_txt = document.getElementById('min_meter_txt');
  var min_meter_input = document.getElementById('min_meter_input');
  console.log(is_visible);
  if (is_visible == false){
    min_meter_txt.innerHTML = "Number of Meters";
    min_meter_input.setAttribute('value','2000');
    // document.getElementById('submit_bttn_div').classList.remove("col-12");
    // document.getElementById('submit_bttn_div').classList.add("col-6");
    document.getElementById('min_meter_parent').classList.remove("col-6");
    document.getElementById('min_meter_parent').classList.add("col-12");
    input.hidden = true;
  }
  else {
    min_meter_txt.innerHTML = "Number of Minutes";
    min_meter_input.setAttribute('value','30');
    // document.getElementById('submit_bttn_div').classList.remove("col-6");
    // document.getElementById('submit_bttn_div').classList.add("col-12");
    document.getElementById('min_meter_parent').classList.remove("col-12");
    document.getElementById('min_meter_parent').classList.add("col-6");
    input.hidden = false;
  }
}


function show_incomplete(bad_elem){
    var name = bad_elem.concat('-red');
    var astrix = document.getElementById(name);
    if (astrix == null){
        var span = document.createElement('span');
        span.style.color = 'red';
        span.id = name;
        span.innerHTML = "*";
        document.getElementById(bad_elem).appendChild(span);
    }
}

function reset_form(){
    // clear html content
    // document.getElementById("add_workout_form").innerHTML = '';
    $("#add_workout_form > div:not(:first)").remove();

    // reset form items
    document.getElementById('units').disabled = false;
    document.getElementById('num_pieces').disabled = false;
    document.getElementById('min_meter_input').disabled = false;
    document.getElementById('second_input').disabled = false;

    // hide seconds input
    document.getElementById('second_input_div').hidden = true;

    // set text to say Meters
    document.getElementById('min_meter_txt').innerHTML = "Number of Meters";

    // set default to 2000
    document.getElementById('min_meter_input').setAttribute('value','2000');

    // display submit button
    document.getElementById('submit_bttn').style.display = 'block';
    $("#submit_bttn_txt").addClass('d-lg-block');

    // check meters selector
    document.getElementById('units').value = 'meters';

    // resize meter input
    document.getElementById('min_meter_parent').classList.remove("col-6");
    document.getElementById('min_meter_parent').classList.add("col-12");
}

function generate_form(){

  // validate form
  var elements = document.getElementById("add_workout_form").elements;
  var post = validate_workout_form(elements);

  if (post == false){
    return false;
  }

  // hide submit button
  document.getElementById('submit_bttn').style.display = 'none';
  $("#submit_bttn_txt").removeClass('d-lg-block');

  var num_pieces = document.getElementById("num_pieces").value;
  var w_type = document.getElementById("units").value;
  var meter_minutes = document.getElementById("min_meter_input").value;

  // <div class="col-auto form-group">
  //   <small class="form-text text-muted" for="num_pieces">Number of Peices</small>
  //   <input type="number" min="1" class="form-control mb-2" id="num_pieces" placeholder="Number of Peices">
  // </div>

  content_div = "<div class=\"col-md-4 form-group ";
  small_class = "\"><small class=\"form-text text-muted\">";
  end_small = "</small>";
  input = "<div class=\"input-group\"><input type=\"number\" min=\"0\" class=\"form-control mb-2\"";
  end_input = "></div>";
  end_content_div = "<small name=\"error\"></small></div>";
  label = "<label class=\"col-form-label col-auto\">"
  end_label = "</label>"

  for (var i = 0; i < num_pieces; i++) {
      var main_div = document.createElement('div');
      main_div.className = 'form-row align-items-top px-2';
      var part1 = "<div class=\"form-group col-auto align-items-center\">" + small_class + "Piece" + end_small + label + (i+1) + end_label + "</div>";
      var part11 = "<div class=\"row justify-content-center mt-2\">" + "<h5>" + "Piece " + (i+1) + "</h5>" + "</div>";

      document.getElementById('units').disabled = true;
      document.getElementById('num_pieces').disabled = true;
      document.getElementById('min_meter_input').disabled = true;
      document.getElementById('second_input').disabled = true;

      var input1 = ""; var input2 = ""; var input3 = "";
      if (w_type == 'minutes'){
          var d_value_1 = document.getElementById('second_input').value;
          input1 = content_div + small_class + "Meters" + end_small + input + "name=\"meters\"" + end_input + end_content_div;
          input2 = content_div + "col-6" + small_class + "Minutes" + end_small + input + "name=\"minutes\" value=\"" + meter_minutes + "\"" + end_input + end_content_div;
          input3 = content_div + "col-6" + small_class + "Seconds" + end_small + input + "step=\"any\"" + "name=\"seconds\" value=\"" + d_value_1 + "\"" + end_input + end_content_div;
      }
      else {
          input1 = content_div + small_class + "Meters" + end_small + input + "name=\"meters\" value=\"" + meter_minutes + "\"" + end_input + end_content_div;
          input2 = content_div + "col-6" + small_class + "Minutes" + end_small + input + "name=\"minutes\"" + end_input + end_content_div;
          input3 = content_div + "col-6" + small_class + "Seconds" + end_small + input + "name=\"seconds\"" + "step=\"any\"" + end_input + end_content_div;
      }

      var header_div = document.createElement('div');
      header_div.innerHTML = "<hr>" +part11;

      main_div.innerHTML = input1 + input2 + input3;

      document.getElementById('add_workout_form').appendChild(header_div);
      document.getElementById('add_workout_form').appendChild(main_div);
  }

  var submit_div = document.createElement('div');
  submit_div.className = 'form-row col mb-2';

  var save_div = document.createElement('div');
  save_div.className = 'col-auto';
  save_div.innerHTML = '<input class=\"btn btn-primary\" type=\"submit\" value=\"Save Workout\">';
  submit_div.appendChild(save_div);

  var reset_div = document.createElement('div');
  reset_div.innerHTML = '<input class=\"btn btn-primary\" type=\"button\" onClick=\"reset_form();\" value=\"Reset\">';
  submit_div.appendChild(reset_div);

  document.getElementById('add_workout_form').appendChild(submit_div);
}

function demoUpload() {
    console.log('upload');

    vEl = document.getElementById('erg-image');
    var $uploadCrop = new Croppie(vEl, {
        enableExif: true,
        viewport: {width: 900, height: 900, type: 'square'},
        boundary: {width: 1000, height: 1000},
        enableOrientation: true
    });

    function readFile(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                $('.upload-demo').addClass('ready');

                $uploadCrop.bind({
                    url: e.target.result,
                    orientation: 1,
                }).then(function () {
                    console.log('jQuery bind complete');
                });
            }

            reader.readAsDataURL(input.files[0]);
            $("#save_erg_image").removeClass('disabled');
            document.getElementById("save_erg_image").hidden = false;
            document.getElementById("rotate").hidden = false;
            $("#load_file").removeClass("col-12");
            $("#load_file").addClass("col-8");
            $('#rotate').on('click', function (ev) {
                $uploadCrop.rotate(90);
            });
        }
        else {
            swal("Sorry - you're browser doesn't support the FileReader API");
        }
    }

    $('#upload').on('change', function () {
        readFile(this);
    });
    $('#save_erg_image').on('click', function (ev) {
        if (!$('#save_erg_image').hasClass('disabled')) {
            $uploadCrop.result({
                type: 'base64',
                size: {width: 1000, height: 1000},
                format: 'jpeg'
            }).then(function (img) {
                $.post('/save_erg_image', {img: img}, function (data, status) {
                    console.log(status);
                    console.log(data['screen_data']);
                });
            });
        }
    });
}