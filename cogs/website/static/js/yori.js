//Tabs for commands
function openCategory(evt, category) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(category).style.display = "block";
    evt.currentTarget.className += " active";

}


//validation function for inputs
function add_validator() {
    $(this).removeClass("input-error")
    message = $(this).val()
    if(message){
        $(this).removeClass("invalid").addClass("valid")
    }
    else {
        $(this).removeClass("valid").addClass("invalid")
    }
}
//add the above validator for all inputs and textareas on load
$(document).ready(function () {
    $('input').on('input', add_validator);
    $('textarea').on('input', add_validator);
});


//check for valid on inputs when submitting
$('input[type=submit]').click(function(event){
    var error_free = true;
    var form=$(this).closest("form").find(':input').each(function(){
        var invalid = $(this).hasClass("invalid")
        if(invalid) {
            error_free = false;
            $(this).addClass("input-error")
        }
    });
    if(!error_free){
        event.preventDefault();
        alert("Input's can not be blank")
    }
});

//Show the guild on select of it
$(document).ready(function () {
  $('#guildSelector').change(function () {
    $('.group').hide();
    $('.'+$(this).val()).show();
  });
});

//Show the save button on prefix input
$(document).ready(function () {
  $('input[type=submit]').hide();
  $('.guild-input').on('input', function () {
    $(this).closest("form").find(':submit').show("normal");
  });
});

//Show the save button on removal of a prefix
$(document).ready(function() {
    $(".prefix-remove").click(function() {
        $(this).closest("form").find(':submit').show("normal");
    });
});

//Remove the prefix div if they want one less
$(document).ready(function() {
    $(".prefix-remove").click(function() {
        $(this).parent("div").remove();
    });
});



//Add the prefix div on click of add button
$(document).ready(function() {
    $(".prefix-add").click(function() {
        $(this).closest("form").find(':submit').show("normal");
        var button = $("<button type=\"button\" class=\"prefix-remove prefix-remove-new btn btn-skin\">-</button>");
        button.click(function() {
            $(this).parent("div").remove();
        });
        var prefix = $("<input class=\"guild-input invalid\" id=\"prefix\" name=\"prefix\" type=\"text\"/>");
        prefix.on('input', function () {
            $(this).closest("form").find(':submit').show("normal");
        });
        prefix.on('input', add_validator);
        var prefix_div = $("<div class=\"prefix-div\"/>");
        prefix_div.append(prefix);
        prefix_div.append(button);
        $(this).parent("div").parent().append(prefix_div);
    });
});


//Remove and save function for welcome fields
function welcome_remove() {
    $(this).closest("form").find(':submit').show("normal");
    $(this).parent().parent().remove();
}

//Remove welcome if button is pressed and show save button
$(document).ready(function() {
    $(".welcome-field-remove-button").click(welcome_remove)
});


function welcome_add() {
   var field_div = $("<div class=\"welcome-field\"/>");
   var button_div = $("<div class=\"welcome-field-button\"/>");
   var button = $("<div type=\"button\" class=\"btn btn-skin-red welcome-field-remove-button\"/>");
   button.click(welcome_remove);
   var glyph_span = $("<span class=\"glyphicon glyphicon-remove\"/>");
   var welcome_field_values = $("<div class=\"welcome-field-values\"/>");
   var field_name_input = $("<input name=\"field-name\" value=\"Enter field name here...\"/>");
   var field_value_span = $("<span class=\"welcome-field-value\"/>");
   var field_value_textarea = $("<textarea class=\"welcome-field-value\" name=\"field-value\">Enter field value here...</textarea>");
   var p = $("<p/>");
   button.append(glyph_span);
   button_div.append(button);
   field_div.append(button_div);
   field_value_span.append(field_value_textarea);
   p.append(field_name_input);
   p.append(field_value_span);
   welcome_field_values.append(p);
   field_div.append(welcome_field_values);
   $(this).parent().append(field_div);
   cloney = $(this).clone()
   cloney.click(welcome_add)
   $(this).parent().append(cloney);
   $(this).closest("form").find(':submit').show("normal");
   $(this).remove();

}

$(document).ready(function() {
    $(".welcome-add").click(welcome_add)
});

