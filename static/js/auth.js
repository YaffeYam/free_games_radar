// Event listener for the registration form submission.
document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission behavior.

    // Collect input data from the registration form fields.
    const data = {
        username: document.getElementById('username').value, // Username entered by the user.
        password: document.getElementById('password').value, // Password entered by the user.
        fullname: document.getElementById('fullname').value // Full name entered by the user.
    };

    // Send a POST request to the server to register the user.
    axios.post('/register', data)
        .then(response => {
            // Show a success message and redirect to the login page after successful registration.
            alert('Registration successful!');
            window.location.href = 'login.html'; // Redirect to the login page.
        })
        .catch(error => {
            // Display an error message if registration fails.
            alert('Error: ' + error.response.data.error);
        });
});

// Event listener for the login form submission.
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission behavior.

    // Collect input data from the login form fields.
    const data = {
        username: document.getElementById('username').value, // Username entered by the user.
        password: document.getElementById('password').value // Password entered by the user.
    };

    // Send a POST request to the server to authenticate the user.
    axios.post('/login', data)
        .then(response => {
            // Show a success message and redirect to the store page after successful login.
            alert('Login successful!');
            window.location.href = 'store.html'; // Redirect to the store page.
        })
        .catch(error => {
            // Display an error message if login fails.
            alert('Error: ' + error.response.data.error);
        });
});

// Event listener for the logout button click.
document.getElementById('logoutButton').addEventListener('click', function() {
    // Send a POST request to the server to log the user out.
    axios.post('/logout')
        .then(response => {
            // Show a success message and redirect to the homepage after successful logout.
            alert('Logout successful!');
            window.location.href = 'index.html'; // Redirect to the homepage.
        })
        .catch(error => {
            // Display an error message if logout fails.
            alert('Error: ' + error.response.data.error);
        });
});
