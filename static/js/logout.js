// Logout functionality
document.getElementById('logoutButton').addEventListener('click', function() {
    // When the logout button is clicked, send a POST request to '/user_logout' to log the user out.
    fetch('/user_logout', { method: 'POST' })
    .then(response => response.json()) // Parse the JSON response from the server.
    .then(data => {
        // If the response contains a 'redirect_url', redirect the user to that URL.
        if (data.redirect_url) {
            window.location.href = data.redirect_url; // Redirect the browser to the new URL.
        }
    })
    .catch(error => {
        // If there is an error during the fetch request (e.g., network issues), log the error to the console.
        console.error('Error logging out:', error); // Log any errors to the console for debugging.
    });
});
