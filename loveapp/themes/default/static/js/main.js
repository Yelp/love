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

/**
 * Initialize autocomplete and other functionality for the love form
 */
function initLoveForm() {
    if (!$('#send-love-form').length) {
        return; // Exit if we're not on a page with the love form
    }

    $('#nav-send').addClass('active');
    $('#secret-love-label').tooltip();
    $('input[name="recipients"]').focus();
    if ($('input[name="recipients"]').val() != '') {
        var messageText = $('textarea[name="message"]').val();
        $('textarea[name="message"]').focus().val('').val(messageText);
    }
    $('#love-error').hide();
    
    // Hashtags autocomplete - code heavily sampled from http://jqueryui.com/autocomplete/#multiple-remote
    $('textarea[name="message"]')
        .bind('keydown', function(event) {
            if (event.keyCode === $.ui.keyCode.TAB &&
                $(this).data("ui-autocomplete").menu.active) {
                event.preventDefault();
            }
        })
        .autocomplete({
            source: function(request, response) {
                $.getJSON('/values/autocomplete', {
                    term: request.term.split(/\s/).pop()
                }, response);
            },
            search: function() {
                var term = this.value.split(/\s/).pop();
                if (!term.startsWith("#")) {
                    return false;
                }
                return term;
            },
            focus: function() { return false; },
            select: function(event, ui) {
                var terms = this.value.split(/\s/);
                terms.pop();
                terms.push(ui.item.value + " ");
                this.value = terms.join(" ");
                return false;
            },
            minLength: 1,
            delay: 5,
            autoFocus: true
        });

    // Recipients autocomplete
    $('input[name="recipients"]')
        // don't navigate away from the field on tab when selecting an item
        .bind('keydown', function(event) {
            if (event.keyCode === $.ui.keyCode.TAB &&
                $(this).autocomplete().menu.active) {
                event.preventDefault();
            }
        })
        .autocomplete({
            source: function(request, response) {
                $.getJSON('/user/autocomplete', {
                    term: extractLast(request.term)
                }, response);
            },
            search: function() {
                // set minLength before attempting autocomplete
                var term = extractLast(this.value);
                if (term.length < 2) {
                    return false;
                }
            },
            focus: function() {
                return false;
            },
            select: function(event, ui) {
                var terms = split(this.value);
                // remove the current input
                terms.pop();
                // add the selected item
                terms.push(ui.item.value);
                // add placeholder to get the comma-and-space at the end
                terms.push('');
                this.value = terms.join(', ');
                return false;
            },
        }).data('ui-autocomplete')._renderItem = function(ul, item) {
            return $("<li>")
                .attr('class', 'ui-menu-item avatar-autocomplete')
                .attr('role', 'presentation')
                .attr("data-value", item.value)
                .append(
                    $("<a>")
                        .attr('class', 'ui-corner-all')
                        .attr('tabindex', '-1')
                        .append(
                            '<img class="img-circle avatar-autocomplete-img" height="25"' +
                            ' src="' + (item.avatar_url || '/_themes/default/img/user_medium_square.png') +
                            '"><span style="vertical-align:middle">' +
                            item.label +
                            '</span>')
                )
                .appendTo(ul);
        };

    // Set up shareable link functionality
    var loveLinkBlock = $('.love-link-block');
    if (loveLinkBlock.length) {
        $('.create-link-btn').hide();
        hideLoveLinkBlockOnInputChange(loveLinkBlock);
        setCopyToClipboardBtnAction();
    }
}

// Helper functions for the love form
function split(val) {
    return val.split(/,\s*/);
}

function extractLast(term) {
    return split(term).pop();
}

function hideLoveLinkBlockOnInputChange(loveLinkBlock) {
    $('input[name="recipients"], textarea[name="message"]').change(function() {
        $('input[name="recipients"], textarea[name="message"]').off('change');
        loveLinkBlock.hide();
        $('.create-link-btn').show();
    });
}

function setCopyToClipboardBtnAction() {
    var copyBtn = document.querySelector('.copybtn');
    copyBtn.addEventListener('click', function() {
        window.getSelection().removeAllRanges();
        var linkText = document.querySelector('.love-link');
        var range = document.createRange();
        range.selectNode(linkText);
        window.getSelection().addRange(range);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
    });
}

function togglePlusOneButton(element) {
    const container = element.closest('.love-plus-one-container');
    const plusOneBtn = container.querySelector('.love-plus-one');
    const confirmForm = container.querySelector('.love-plus-one-confirm');

    if (confirmForm.style.display === 'none') {
        plusOneBtn.style.display = 'none';
        confirmForm.style.display = 'inline-block';
    } else {
        plusOneBtn.style.display = 'inline-block';
        confirmForm.style.display = 'none';
    }
}
function checkUserListCollapsible(userList) {
    if (!userList) return;
    const badges = Array.from(userList.querySelectorAll('.badge'));
    const expander = userList.querySelector('.user-list-expander');
    const gradient = userList.querySelector('.user-list-gradient');
    if (badges.length < 2) {
        userList.classList.remove('is-collapsible', 'user-list-expanded');
        if (expander) expander.style.display = "none";
        if (gradient) gradient.style.display = "none";
        return;
    }
    const firstTop = badges[0].offsetTop;
    const wraps = badges.some(badge => badge.offsetTop > firstTop);
    if (wraps) {
        userList.classList.add('is-collapsible');
        if (expander) expander.style.display = "inline-block";
        if (gradient) gradient.style.display = "block";
    } else {
        userList.classList.remove('is-collapsible', 'user-list-expanded');
        if (expander) expander.style.display = "none";
        if (gradient) gradient.style.display = "none";
    }
}

function toggleUserList(expanderBtn) {
    const userList = expanderBtn.closest('.user-list');
    const expanded = userList.classList.toggle('user-list-expanded');
    if (expanded) {
        expanderBtn.classList.add('chevron-rotated');
        expanderBtn.setAttribute('aria-expanded', 'true');
        userList.style.maxHeight = ''; // reset for measuring actual height
        let fullHeight = userList.scrollHeight;
        userList.style.maxHeight = fullHeight + "px"; // animate open!
    } else {
        expanderBtn.classList.remove('chevron-rotated');
        expanderBtn.setAttribute('aria-expanded', 'false');
        userList.style.maxHeight = ''; // REMOVE so it falls back to CSS (collapsed) height
    }
}

window.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.user-list').forEach(checkUserListCollapsible);
});
window.addEventListener('resize', function() {
    document.querySelectorAll('.user-list').forEach(checkUserListCollapsible);
});

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
tooltipTriggerList.forEach(function (tooltipTriggerEl) {
  new bootstrap.Tooltip(tooltipTriggerEl)
})

$(document).ready(function () {
    setupDateFormatting();
    setupLinkify();
    initLoveForm(); // Add the initialization of the love form
});
