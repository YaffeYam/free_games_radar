// Event listener for the registration form submission
document.getElementById('registrationForm').addEventListener('submit', function(event) {
    // Prevent the default form submission to handle it with JavaScript
    event.preventDefault();

    // Create a new FormData object to collect form data
    const formData = new FormData(this);

    // Get the username entered in the form
    const username = formData.get('username');

    // Get the spinner element to show a loading animation during the process
    const spinner = document.getElementById('spinner');
    spinner.classList.add('show'); // Show the spinner

    // Check if the username is unique by sending a GET request to the server
    fetch(`/check_username/${username}`, {
        method: 'GET'
    })
    .then(response => response.json()) // Parse the response as JSON
    .then(data => {
        // If the username is already taken, display an error message
        if (data.status === 'error') {
            const messageElement = document.getElementById('message');
            messageElement.textContent = data.message; // Display the error message
            messageElement.className = 'message error'; // Add the error class for styling
            spinner.classList.remove('show'); // Hide the spinner
        } else {
            // If the username is available, proceed with the registration process
            fetch('/user_register', {
                method: 'POST',
                body: formData // Send the form data to the server
            })
            .then(response => response.json()) // Parse the server's response
            .then(data => {
                const messageElement = document.getElementById('message');
                messageElement.textContent = data.message; // Display the response message
                messageElement.className = data.status == "success" ? 'message success' : 'message error'; // Show success or error message based on status
                if (data.status == "success") {
                    // If registration is successful, redirect to the login page after a short delay
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1000);
                }
            })
            .catch(error => {
                // Log any errors that occur during the registration process
                console.error('Error:', error);
                document.getElementById('message').textContent = 'An unexpected error occurred.'; // Display an error message
                document.getElementById('message').className = 'message error'; // Set the error message class
            })
            .finally(() => {
                // Remove the spinner once the process is completed (either success or failure)
                spinner.classList.remove('show');
            });
        }
    })
    .catch(error => {
        // Log any errors that occur during the username check
        console.error('Error:', error);
        document.getElementById('message').textContent = 'An unexpected error occurred.'; // Display a generic error message
        document.getElementById('message').className = 'message error'; // Set the error message class
        spinner.classList.remove('show'); // Hide the spinner if an error occurs
    });
});
