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
    message = $(this).val()
    if(message){
        $(this).removeClass("invalid").addClass("valid")
    }
    else {
        $(this).removeClass("valid").addClass("invalid")
    }
}

//check for valid on inputs when submitting
$('input[type=submit]').click(function(event){
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

$(document).ready(function () {
    $('input').on('input', add_validator);
});


$(document).ready(function () {
  $('.group').hide();
  $('#guildSelector').change(function () {
    $('.group').hide();
    $('.'+$(this).val()).show();
  });
  $("#guildSelector").val($("#guildSelector option:first").val());
});

//Show the save button on prefix input
$(document).ready(function () {
  $('input[type=submit]').hide();
  $('.guild-input').on('input', function () {
    $(this).closest("form").find(':submit').show("normal");
  });
});


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
        var button = $("<button type=\"button\" class=\"prefix-remove btn btn-skin\">-</button>");
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

//welcome functions
$('body').on('click', '.welcome-text', function(){
	var save_func = function(){
  	$heading = $("<p/>").text($(this).val())
    $button = $("<button type=\"button\" class=\"welcome-text btn btn-skin\"/>").
    $button.append('<span class=\"glyphicon glyphicon-cog\"></span>')
    $heading.append($button)
    $(this).replaceWith($heading)
  }
  $heading = $(this).parent()
  $(this).remove()
  $input = $('<input/>').val($heading.text())
  $input.one('blur', save_func).focus();
  $heading.replaceWith($input)
});




