(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        // The function to hide the spinner after a short timeout
        setTimeout(function () {
            // Check if the spinner element exists on the page
            if ($('#spinner').length > 0) {
                // Remove the 'show' class from the spinner to hide it
                $('#spinner').removeClass('show');
            }
        }, 1); // Delay of 1 millisecond before executing the function
    };
    spinner(); // Call the spinner function to hide the spinner

    // Sidebar Toggler
    $('.sidebar-toggler').click(function () {
        // Toggle the 'open' class on the sidebar and content when the sidebar toggler is clicked
        $('.sidebar, .content').toggleClass("open");
        return false; // Prevent the default action of the click event
    });

})(jQuery);
