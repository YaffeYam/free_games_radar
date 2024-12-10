// Add a 'submit' event listener to the login form.
document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent the default form submission behavior (page reload).

    // Collect the form data using FormData API.
    const formData = new FormData(this);

    try {
        // Send an asynchronous POST request to the '/user_login' endpoint with the form data.
        const response = await fetch('/user_login', {
            method: 'POST', // HTTP method for the request.
            body: formData  // Attach the form data as the request body.
        });

        const messageElement = document.getElementById('message'); // Locate the message element for displaying feedback.
        const result = await response.json(); // Parse the response JSON.

        if (response.ok) {
            // If the response is successful, redirect the user based on their role.
            // Redirect to the admin dashboard if the user is an admin, otherwise redirect to the user dashboard.
            window.location.href = result.isAdmin ? '/admin_dashboard' : '/user_dashboard';
        } else {
            // If the login fails, display an error message to the user.
            messageElement.textContent = result.error || 'Login failed. Please try again.'; // Show the error message from the server or a default message.
            messageElement.className = 'message error'; // Apply an error-specific CSS class for styling.
        }
    } catch (error) {
        // Handle any errors that occur during the fetch request.
        console.error('Error:', error); // Log the error details to the console for debugging.

        // Display a generic error message for unexpected issues.
        const messageElement = document.getElementById('message');
        messageElement.textContent = 'An unexpected error occurred. Please try again.';
        messageElement.className = 'message error'; // Apply an error-specific CSS class for styling.
    }
});
