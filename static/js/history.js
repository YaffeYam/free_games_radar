// When the DOM content is fully loaded, execute the following logic.
document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Make an asynchronous GET request to fetch the user's purchase history.
        const response = await axios.get('/user/purchase_history');

        // Check if the response contains a history array with items.
        if (response.data.history && response.data.history.length > 0) {
            const purchaseHistoryContainer = document.getElementById('purchaseHistory'); // Locate the container for displaying the purchase history.

            // Iterate through each item in the purchase history and create an HTML element to display it.
            response.data.history.forEach(item => {
                const purchaseItem = document.createElement('div'); // Create a new div for each purchase item.
                purchaseItem.classList.add('purchase-item'); // Add a CSS class for styling the purchase item.

                // Set the inner HTML of the purchase item to include the game's name, price, and purchase date.
                purchaseItem.innerHTML = `
                    <h3>${item.game_name}</h3>
                    <p>Price: $${item.price}</p>
                    <p>Purchased on: ${new Date(item.timestamp).toLocaleDateString()}</p>
                `;

                // Append the purchase item to the container.
                purchaseHistoryContainer.appendChild(purchaseItem);
            });
        } else {
            // If no purchase history is found, display a message indicating the absence of records.
            document.getElementById('purchaseHistory').innerHTML = '<p>No purchase history found.</p>';
        }
    } catch (error) {
        // Log the error and display a message indicating a failure to fetch the purchase history.
        console.error('Error fetching purchase history:', error);
        document.getElementById('purchaseHistory').innerHTML = '<p>Error fetching purchase history. Please try again later.</p>';
    }
});

// Add an event listener to the logout button to handle user logout.
document.getElementById('logoutButton').addEventListener('click', async () => {
    try {
        // Make an asynchronous POST request to log the user out.
        await axios.post('/logout'); // Adjust the endpoint if necessary.
        window.location.href = 'login.html'; // Redirect the user to the login page after successful logout.
    } catch (error) {
        // Log any errors encountered during the logout process.
        console.error('Error logging out:', error);
    }
});
