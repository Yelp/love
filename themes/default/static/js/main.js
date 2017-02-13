function setupDateFormatting() {
    var today = new Date();
    today.setHours(0,0,0,0);
    var yesterday = new Date(today.getTime() - 86400000);
    $('span.nicetime').each(function(elem) {
        var d = new Date(parseInt($(this).text(), 10));
        var dateStr = '';
        var preDateStr = '';
        if (d.compareTo(today) >= 0) {
            dateStr = 'today';
        } else if (d.compareTo(yesterday) >= 0) {
            dateStr = 'yesterday';
        } else {
            preDateStr = 'on ';
            dateStr = d.toString('MMM d, yyyy');
        }

        var timeStr = d.toString('h:mm tt');
        $(this).text(preDateStr + dateStr + ' at ' + timeStr);
    });
}

function setupLinkify() {
    $('.love-message').linkify();
}

$(document).ready(function () {
    setupDateFormatting();
    setupLinkify();
});
