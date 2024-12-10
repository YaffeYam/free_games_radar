window.onload = function () {
    // Fetch purchase history when the page loads
    fetchPurchaseHistory();
};

function fetchPurchaseHistory() {
    // Make an HTTP GET request to fetch purchase history data
    axios.get('/purchase_history_data')
        .then(response => {
            console.log("response: ", response); // Log the response for debugging purposes
            const history = response.data.games; // Extract the 'games' data from the response
            const purchaseHistoryContainer = document.getElementById('purchaseHistory'); // Get the container to display history

            // Clear any existing content in the container
            purchaseHistoryContainer.innerHTML = '';

            // Check if there are no purchase records
            if (history.length === 0) {
                // If no purchases, display a message indicating no games have been purchased yet
                purchaseHistoryContainer.innerHTML = '<p>No games purchased yet :(</p>';
            } else {
                // Iterate over each item in the purchase history
                history.forEach(item => {
                    // Create a new div for each purchase history item
                    const historyItem = document.createElement('div');
                    historyItem.className = 'purchase-history-item'; // Add a class for styling

                    // If 'user_name' exists in the item, display it along with other details
                    const userInfo = item.user_name ? `<strong>User:</strong> ${item.user_name} <br>` : '';

                    // Set the inner HTML of the history item with relevant information
                    historyItem.innerHTML = `
                        <p>
                            ${userInfo}
                            <strong>Game:</strong> ${item.game_name} <br>
                            <strong>Purchase Date:</strong> ${new Date(item.purchase_timestamp).toLocaleString()} <br>
                            <strong>Price:</strong> $${item.price.toFixed(2)} <!-- Format price to 2 decimal places -->
                        </p>
                    `;
                    // Append the history item to the container
                    purchaseHistoryContainer.appendChild(historyItem);
                });
            }
        })
        .catch(error => {
            // Log any errors that occur during the request
            console.error('Error fetching purchase history:', error);
        });
}
