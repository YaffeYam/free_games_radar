// Add event listener to fetch revenue stats when the page has fully loaded
window.addEventListener('load', function() {
    // Call function to fetch and display revenue statistics
    fetchRevenueStats();
});

// Function to fetch revenue statistics from the server
function fetchRevenueStats() {
    // Send a GET request to fetch revenue stats from the server
    axios.get('/admin/revenue-stats')
        .then(response => {
            // Extract the stats from the response data
            const stats = response.data;

            // Update the HTML elements with the fetched stats
            // Display today's sales in the 'todaySale' element, formatting the value as currency
            document.getElementById('todaySale').innerText = `$${stats.today_sales.toFixed(2)}`;

            // Display total sales in the 'totalSale' element, formatting the value as currency
            document.getElementById('totalSale').innerText = `$${stats.total_sales.toFixed(2)}`;

            // Display today's revenue in the 'todayRevenue' element, formatting the value as currency
            document.getElementById('todayRevenue').innerText = `$${stats.today_revenue.toFixed(2)}`;

            // Display total revenue in the 'totalRevenue' element, formatting the value as currency
            document.getElementById('totalRevenue').innerText = `$${stats.total_revenue.toFixed(2)}`;
        })
        .catch(error => {
            // Log any errors that occur during the fetch operation
            console.error('Error fetching revenue stats:', error);
        });
}
