// Function to highlight the selected avatar by adding a blue border
function selectAvatar(img) {
    // Remove the border from all avatar images
    document.querySelectorAll('.img-thumbnail').forEach(el => el.style.border = "none");

    // Add a blue border to the clicked avatar image
    img.style.border = "2px solid #007bff";
}

// Event listener for form submission to handle avatar selection
document.getElementById('avatar-form').addEventListener('submit', async function (event) {
    // Prevent the default form submission behavior (page reload)
    event.preventDefault();

    // Get the selected avatar from the radio buttons
    const selectedAvatar = document.querySelector('input[name="user_avatar"]:checked');

    // If no avatar is selected, show an alert and stop the form submission
    if (!selectedAvatar) {
        alert('Please select an avatar.');
        return;
    }

    // Prepare the data to send in the form, appending the selected avatar value
    const formData = new FormData();
    formData.append('user_avatar', selectedAvatar.value);

    try {
        // Make an AJAX POST request to update the avatar on the server
        const response = await axios.post('/update_user_avatar', formData);

        // Handle the server response
        if (response.data.status === 'success') {
            // If avatar update is successful, get the new avatar URL from the response
            const newAvatarUrl = response.data.updated_avatar_url;

            // Update all avatar images on the page with the new avatar URL
            document.querySelectorAll('.avatar-img').forEach(img => {
                img.src = newAvatarUrl;
            });

            // Close the avatar selection modal using Bootstrap's modal method
            const avatarModal = bootstrap.Modal.getInstance(document.getElementById('avatarModal'));
            avatarModal.hide();

            // Display success feedback to the user
            alert("Avatar changed successfully");
        } else {
            // If there's an error from the server, display the error message
            alert(response.data.message);
        }
    } catch (error) {
        // Log any errors that occur during the request and show an error alert
        console.error(error);
        alert('An error occurred while updating the avatar.');
    }
});
