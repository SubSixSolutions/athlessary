function validate_workout_form(elements){
  var post = true;
  for (var i = 0, element; element = elements[i++];) {
      console.log(element.value);
      // if (element.name.includes('seconds') || element.name.includes('minutes') ||
      //       element.name.includes('meters') || element.name.includes('date')
      //       || element.name.includes('time')
      // ){
      if (!element.name.includes('units') && element.type != 'button'){
          console.log(element.parentElement.parentElement);
          var p = element.parentElement.parentElement.querySelector('small[name="error"]');
          if (element.value == ""){
            element.classList.add("border-danger");
            p.className = "text-danger";
            p.innerHTML = "Input Required.";
            post = false;
          }
          else if (element.name.includes('seconds') && element.value > 59) {
            element.classList.add("border-danger");
            p.className = "text-danger";
            p.innerHTML = "Value must be less than 60.";
            post = false;
          }
          else {
            p.innerHTML = "";
            p.className = "";
            element.classList.remove("border-danger");
          }
      }
  }
  return post;
}
