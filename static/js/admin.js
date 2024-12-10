// Wait until the DOM content is fully loaded before executing the script.
document.addEventListener('DOMContentLoaded', function() {
    
    // Use Axios to send a GET request to the backend API endpoint for fetching user data.
    axios.get('/admin/users')
        .then(response => {
            // Select the container element in the HTML where the user information will be displayed.
            const usersList = document.getElementById('usersList');

            // Loop through the response data (list of users) received from the backend.
            response.data.forEach(user => {
                // Create a new HTML element to hold information for each user.
                const userItem = document.createElement('div');

                // Populate the created element with the user's details, such as username, full name, and admin status.
                userItem.innerHTML = `
                    <p>Username: ${user.username}</p>
                    <p>Full Name: ${user.fullname}</p>
                    <p>Admin: ${user.is_admin ? 'Yes' : 'No'}</p>
                    <hr>
                `;

                // Append the populated user item to the main container in the HTML.
                usersList.appendChild(userItem);
            });
        })
        .catch(error => {
            // Handle errors that may occur during the API request.
            // Display an alert with the error message retrieved from the server response.
            alert('Error: ' + error.response.data.error);
        });
});
