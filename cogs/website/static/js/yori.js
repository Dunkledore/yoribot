function editInput(inputId, glyphId) {
    var inputIdWithHash = "#" + inputId;
    var glpyhIdWithHash = "#" + glyphId;
    var elementValue = $(inputIdWithHash).val();
    $(inputIdWithHash).replaceWith('<input onfocusout="lockInput(\''+ inputId + '\',\'' + glyphId + '\')" name="test" id="' + inputId + '" value="' + elementValue + '">');
    $(inputIdWithHash).focus();
    $(glpyhIdWithHash).replaceWith('');
}

function lockInput(inputId, glyphId) {
	var inputIdWithHash = "#" + inputId;
    var glpyhIdWithHash = "#" + glyphId;
    var elementValue = $(inputIdWithHash).val();
    var inputString = '<input readonly id=' + inputId + ' value="' + elementValue + '">'
    var glpyhString = '<span id="' + glyphId + '" class="glyphicon glyphicon-pencil" onclick="editInput(\'' + inputId + '\', \''+ glyphId + '\')">'
    $(inputIdWithHash).replaceWith(inputString + glpyhString)
}
//Show the correct guild using a drop down
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

//Remove the prefix div if they want one less
$(document).ready(function() {
    $(".prefix-remove").click(function() {
        $(this).parent("div").remove();
    });
});


//Add the prefix div on click of add button
$(document).ready(function() {
    $(".prefix-add").click(function() {
        var button = $("<button type=\"button\" class=\"prefix-remove prefix-button\">-</button>");
        button.click(function() {
            $(this).parent("div").remove();
        });
        var prefix = $("<input class=\"prefix guild-input\" id=\"prefix\" name=\"prefix\" type=\"text\"/>");
        prefix.on('input', function () {
            $(this).closest("form").find(':submit').show("normal");
        });
        var prefix_div = $("<div class=\"prefix-div\"/>");
        prefix_div.append(prefix);
        prefix_div.append(button);
        $(this).parent("div").parent().append(prefix_div);
    });
});

//welcome functions
$('body').on('click', '.welcome-text', function(){
	var save_func = function(){
  	$heading = $("<h3/>").text($(this).val())
    $button = $("<button class=\"welcome_text\"/>").text("Cogs")
    $heading.append($button)
    $(this).replaceWith($heading)
  }
  $heading = $(this).parent()
  $(this).remove()
  $input = $('<input/>').val($heading.text())
  $input.one('blur', save_func).focus();
  $heading.replaceWith($input)
});





