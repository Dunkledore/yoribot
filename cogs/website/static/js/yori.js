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
  })
});

$(document).ready(function () {
  $('input[type=submit]').hide();
  $('.prefix').on('input', function () {
    $(this).closest("form").find(':submit').show("slow");
  })
});

