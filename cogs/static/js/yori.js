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

