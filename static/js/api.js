// Run the `fetchAndDisplayGames` function automatically when the page loads.
window.onload = function() {
    console.log('fetchAndDisplayGames');
    fetchAndDisplayGames(); // Initial call to fetch games without filters.
};

/**
 * Fetches and displays games from the API based on the selected filters.
 * @param {string} filterType - The type of filter to apply (e.g., 'category', 'platform', 'sort-by').
 */
async function fetchAndDisplayGames(filterType = '') {
    const spinner = document.getElementById('spinner'); // Element to indicate loading.
    const gameList = document.getElementById('game-list'); // Container for displaying the game cards.

    // Show the loading spinner while fetching data.
    spinner.style.visibility = 'visible';

    // Base API URL for fetching games.
    let url = 'https://free-to-play-games-database.p.rapidapi.com/api/games';

    // Get filter values from the corresponding dropdown menus.
    const category = document.getElementById('category-select').value;
    const platform = document.getElementById('platform-select').value.toLowerCase();
    const sortBy = document.getElementById('sort-select').value;

    // Dynamically append query parameters to the URL based on the filter type.
    if (filterType === 'category' && category) {
        url += `?category=${category}`;
    } else if (filterType === 'platform' && platform) {
        url += `?platform=${platform}`;
    } else if (filterType === 'sort-by' && sortBy) {
        url += `?sort-by=${sortBy}`;
    }

    // Options for the API request, including the necessary headers for authentication.
    const options = {
        method: 'GET',
        url: url,
        headers: {
            'X-RapidAPI-Key': '2d889234d9msh312fabeba309c74p17155fjsn0cb8d4ac8083', // API key for authentication.
            'X-RapidAPI-Host': 'free-to-play-games-database.p.rapidapi.com' // Host for the FreeToGame API.
        }
    };

    // Make the API request using Axios.
    axios.request(options)
        .then(response => {
            const games = response.data; // Store the fetched games data.

            // Hide the loading spinner once data is received.
            spinner.style.visibility = 'hidden';

            // Clear the current game list to populate with new data.
            gameList.innerHTML = '';

            // Loop through the games and dynamically create cards for each.
            games.forEach(game => {
                const gameCard = document.createElement('div'); // Create a container for the game card.
                gameCard.classList.add('col-lg-3', 'col-md-4', 'col-sm-6', 'mb-4'); // Add responsive grid classes.

                // Populate the card with game information.
                gameCard.innerHTML = `
                    <div class="card h-100 shadow-sm">
                        <img src="${game.thumbnail}" alt="${game.title}" class="card-img-top">
                        <div class="card-body">
                            <h5 class="card-title">${game.title}</h5>
                            <p class="card-text"><strong>Genre:</strong> ${game.genre}</p>
                            <p class="card-text"><strong>Platform:</strong> ${game.platform}</p>
                        </div>
                        <div class="card-footer text-center">
                            <a href="${game.game_url}" target="_blank" class="btn btn-primary">Play Now</a>
                        </div>
                    </div>
                `;
                // Append the card to the game list container.
                gameList.appendChild(gameCard);
            });
        })
        .catch(error => {
            // Log errors to the console for debugging purposes.
            console.error('Error fetching games:', error);

            // Hide the spinner and display an error message if the request fails.
            spinner.style.visibility = 'hidden';
            gameList.innerHTML = '<p>Sorry, failed to load games. Please try again later.</p>';
        })
        .finally(() => {
            // Ensure the spinner is hidden, even if an error occurs.
            spinner.style.visibility = 'hidden';
        });
}
