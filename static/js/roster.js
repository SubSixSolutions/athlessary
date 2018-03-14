$(window).ready(function () {
    initialize_roster();
});

function drag_select() {
    let isMouseDown = false,
        isHighlighted;
    let table_body = $("#athlete_table").find("tbody tr");
    let table_head = $("#athlete_table").find("thead");

    table_head.mousedown(function () {
        return false;
    });

    table_body.mousedown(function () {
        isMouseDown = true;
        $(this).toggleClass("bg-info");
        isHighlighted = $(this).hasClass("bg-info");
        return false; // prevent text selection
    });

    table_body.mouseover(function () {
        if (isMouseDown) {
            $(this).toggleClass("bg-info", isHighlighted);
            console.log(this);
        }
    });

    table_body.bind("selectstart", function () {
        return false;
    });

    $(document).mouseup(function () {
        isMouseDown = false;
    });
}

function on_submit() {
    let table =  document.getElementById('athlete_table');
    let tableRows = table.rows;
    let athletes = [];
    let drivers = [];
    for(let i = 1; i < tableRows.length; i++) {
        let id = tableRows[i].id;
        let row = document.getElementById(id.toString());
        let going = row.classList.contains('bg-info');
        let checkBox = row.children[3].children[0];
        let driving = false;
        if (checkBox) {
           driving = checkBox.checked;
        }
        let going_string = going ? "is going to practice" : "";
        let driving_string = driving ? "and is driving" : "";
        //console.log('Athlete', id, going_string, driving_string);
        if(going) {
            if(driving) {
                drivers.push(id);
            } else {
                athletes.push(id);
            }
        }
    }
    //console.log(athletes);
    //let json = JSON.stringify(athletes);
    //console.log(json);

    $.post('/drivers', {athletes: athletes, drivers:drivers});
    return false;
}
function submit_success() {
    console.log('success');
    window.location.replace("/drivers");
}

function initialize_roster() {
    $.get('/get_all_athletes', function (data, status) {
        for (let i = 0; i < data.length; i++) {
            let newRow = document.createElement("tr");
            let cols = "";
            newRow.id = data[i]['user_id'];
            let nameCell = newRow.insertCell(0);
            nameCell.innerHTML = '<td class=\"align-middle\">' + data[i]['first'] + '</td>';
            nameCell.classList.add("align-middle");
            let addressCell = newRow.insertCell(1);
            addressCell.innerHTML = '<td class=\"align-middle\">' + data[i]['address'] + '</td>';
            let seatsCell = newRow.insertCell(2);
            seatsCell.innerHTML = '<td class=\"text-center\">' + data[i]['num_seats'] + '</td>';

            let drivingCell = newRow.insertCell(3);
            drivingCell.innerHTML = '<td class=\"text-center\">';
            if (data[i]['num_seats'] > 0) {
                let drivingButton = document.createElement('input');
                drivingButton.type = "checkbox";
                drivingButton.autocomplete = "off";
                drivingButton.classList.add("text-center");
                drivingCell.appendChild(drivingButton);
            }
            //newRow.append(cols);
            $("#athlete_table").find("tbody").append(newRow);
        }
        $(drag_select);
        document.getElementById("done_button").onclick = on_submit;
    });
}


