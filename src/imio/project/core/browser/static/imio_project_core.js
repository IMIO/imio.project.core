$(document).ready(function(){
    /* by default, table with 'listing nosort' are not oddevened... */
    $('table.listing tbody').each(setoddeven);
});

/* helper function that set odd/ven class on rows of a table having the 'listing' class */
function setoddeven() {
    var tbody = $(this);
    // jquery :odd and :even are 0 based
    tbody.find('tr').removeClass('odd').removeClass('even')
        .filter(':odd').addClass('even').end()
        .filter(':even').addClass('odd');
}
