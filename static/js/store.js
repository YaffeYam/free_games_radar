// The window.onload event ensures that the functions are called once the page has fully loaded
window.onload = function() {
    fetchAndDisplayGameStore(); // Fetch and display the games from the store
    formatExpirationDate();     // Format the expiration date input for the payment form
    preventNonNumericInput();   // Prevent non-numeric input in payment form fields
};

// Function to prevent non-numeric input in the card number and CVV fields
function preventNonNumericInput() {
    const cardNumberInput = document.getElementById('cardNumber');
    const cvvInput = document.getElementById('cvv');

    // Prevent non-numeric characters in the Card Number field
    cardNumberInput.addEventListener('input', function(event) {
        cardNumberInput.value = cardNumberInput.value.replace(/\D/g, ''); // Replace non-numeric characters with empty string
    });

    // Prevent non-numeric characters in the CVV field
    cvvInput.addEventListener('input', function(event) {
        cvvInput.value = cvvInput.value.replace(/\D/g, ''); // Replace non-numeric characters with empty string
    });
}

// Function to format the expiration date input into MM/YY format
function formatExpirationDate() {
    const expirationDateInput = document.getElementById('expirationDate');

    expirationDateInput.addEventListener('input', function(event) {
        let value = expirationDateInput.value.replace(/\D/g, ''); // Remove non-digit characters

        // Format the value as MM/YY, adding a slash after the month part
        if (value.length > 2) {
            value = value.slice(0, 2) + '/' + value.slice(2, 4);
        }

        // Limit the length to 5 characters (MM/YY format)
        expirationDateInput.value = value.slice(0, 5);
    });
}

// Function to handle the game purchase process
function buyGame(gameId) {
    // Show the payment modal for game purchase
    const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));
    paymentModal.show();

    // Attach a submit event to the payment form to handle the form submission
    const paymentForm = document.getElementById('payment-form');
    paymentForm.onsubmit = function (event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Get form values
        const cardHolderName = document.getElementById('cardHolderName');
        const cardNumber = document.getElementById('cardNumber');
        const expirationDate = document.getElementById('expirationDate');
        const cvv = document.getElementById('cvv');
        const paymentResult = document.getElementById('payment-result');

        // Clear previous messages and error styles
        paymentResult.innerHTML = '';
        [cardHolderName, cardNumber, expirationDate, cvv].forEach(input => input.classList.remove('is-invalid'));

        // Validation for form fields
        let isValid = true;

        // Check if the cardholder name is provided
        if (!cardHolderName.value.trim()) {
            cardHolderName.classList.add('is-invalid');
            isValid = false;
        }
        // Check if the card number is a valid 16-digit number
        if (!/^\d{16}$/.test(cardNumber.value)) {
            cardNumber.classList.add('is-invalid');
            isValid = false;
        }
        // Check if the expiration date is in MM/YY format
        if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(expirationDate.value)) {
            expirationDate.classList.add('is-invalid');
            isValid = false;
        }
        // Check if the CVV is a valid 3-digit number
        if (!/^\d{3}$/.test(cvv.value)) {
            cvv.classList.add('is-invalid');
            isValid = false;
        }

        // If any field is invalid, return without processing the payment
        if (!isValid) return;

        // Simulate a purchase by sending a POST request to the backend
        axios.post(`/buy/${gameId}`)
            .then(response => {
                // If the purchase is successful, show a success message
                paymentResult.innerHTML = ` 
                    <div class="alert alert-success" role="alert">
                        Game purchased successfully!
                    </div>
                `;

                // Reset the form after a successful purchase
                paymentForm.reset();

                // Dynamically change the button text to "Play" and update its style
                const gameButton = document.querySelector(`[data-game-id="${gameId}"]`);
                if (gameButton) {
                    gameButton.textContent = "Play";
                    gameButton.classList.remove('btn-primary');
                    gameButton.classList.add('btn-success');
                    gameButton.onclick = () => {
                        // Redirect to the play page for the purchased game
                        window.location.href = `/play/${gameId}`;
                    };
                }

                // Hide the modal after a short delay and refresh the game store
                setTimeout(() => {
                    fetchAndDisplayGameStore(); // Refresh the game store to reflect changes
                    paymentModal.hide(); // Hide the payment modal
                    paymentResult.innerHTML = ''; // Clear the success message
                }, 2000);
            })
            .catch(error => {
                // If an error occurs, show an error message
                paymentResult.innerHTML = ` 
                    <div class="alert alert-danger" role="alert">
                        Error processing payment: ${error.response?.data?.error || 'Unknown error'}.
                    </div>
                `;
            });
    };
}

// Function to fetch and display the games available in the store
async function fetchAndDisplayGameStore(filterType = '') {
    const spinner = document.getElementById('spinner');
    const gameList = document.getElementById('game-list');

    // Show the spinner while the data is loading
    spinner.style.visibility = 'visible';

    // Fetch the game data from the backend
    axios.get('/store')
        .then(response => {
            const games = response.data.games;

            // Hide the spinner after data is loaded
            spinner.style.visibility = 'hidden';

            // Populate the game list with the fetched data
            gameList.innerHTML = '';
            games.forEach(game => {
                const gameCard = document.createElement('div');
                gameCard.classList.add('col-lg-3', 'col-md-4', 'col-sm-6', 'mb-4');
            
                // Decide whether to show "Play" or "Buy" button based on whether the game has been purchased
                const actionButton = game.purchased
                ? `<a href="/play/${game.game_name}" target="_blank" class="btn btn-primary">Play Now</a>`
                : `<button onclick="buyGame(${game.id})" class="btn btn-success">Buy</button>`;

                // Create the HTML structure for each game card
                gameCard.innerHTML = `
                    <div class="card h-100 shadow-sm">
                        <img src="/static/games_thumbnails/${game.thumbnail}" alt="${game.game_name}" class="game-thumbnail">
                        <div class="card-body">
                            <h5 class="card-title">${game.game_name}</h5>
                            <p class="card-text"><strong>Price:</strong> $${game.price}</p>
                            <p class="card-text"><strong>Purchased:</strong> ${game.purchased ? 'Yes' : 'No'}</p>
                        </div>
                        <div class="card-footer text-center">
                            ${actionButton}
                        </div>
                    </div>
                `;
                
                // Append the game card to the game list
                gameList.appendChild(gameCard);
            });
        })
        .catch(error => {
            // Handle any errors that occur during the fetch
            console.error('Error fetching games:', error);
            spinner.style.visibility = 'hidden';
            gameList.innerHTML = '<p>Sorry, failed to load games. Please try again later.</p>';
        })
        .finally(() => {
            // Ensure the spinner is hidden after the fetch operation is complete
            spinner.style.visibility = 'hidden';
        });
}
