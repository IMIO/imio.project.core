$(document).ready(function(){
    /* by default, table with 'listing nosort' are not oddevened... */
    $('table.listing tbody').each(setoddeven);
});
