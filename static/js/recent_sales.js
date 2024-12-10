window.addEventListener('load', function() {
    // Call the fetchRecentSales function when the page loads
    fetchRecentSales();
});

function fetchRecentSales() {
    // Send a GET request to fetch recent sales data from the backend
    fetch('/admin/recent-sales')
        .then(response => {
            // Log the response status to the console for debugging purposes
            console.log("Response Status:", response.status);
            return response.json(); // Parse the response as JSON
        })
        .then(data => {
            // Log the fetched data to the console for debugging purposes
            console.log("Fetched Sales Data:", data); 

            // Get the table body element where sales data will be inserted
            const tableBody = document.getElementById('recent-sales-body');
            
            // Clear any previous sales data from the table
            tableBody.innerHTML = '';

            // Check if there is no sales data in the response
            if (data.length === 0) {
                // If no sales data, display a message indicating no data is available
                tableBody.innerHTML = '<tr><td colspan="6">No recent sales data available.</td></tr>';
                return;
            }

            // Loop through each sale in the fetched data and create a table row for each
            data.forEach(sale => {
                const row = document.createElement('tr'); // Create a new row for each sale
                row.innerHTML = `
                    <td>${sale.date}</td>  <!-- Sale date -->
                    <td>${sale.invoice}</td>  <!-- Invoice number -->
                    <td>${sale.customer}</td>  <!-- Customer name -->
                    <td>${sale.amount}</td>  <!-- Sale amount -->
                    <td>${sale.status}</td>  <!-- Sale status -->
                `;
                // Append the newly created row to the table body
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            // If there's an error with the fetch request, log it to the console
            console.error('Error fetching recent sales:', error);
        });
}
