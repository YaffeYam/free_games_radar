// Wait until the DOM is fully loaded before executing the script
document.addEventListener('DOMContentLoaded', () => {
    // Get references to the sidebar, main content, toggle button, and sidebar links
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const toggleButton = document.getElementById('sidebarToggle');
    const sidebarLinks = sidebar.querySelectorAll('a');

    // Add event listener to the toggle button to open or collapse the sidebar
    toggleButton.addEventListener('click', () => {
        // Toggle 'collapsed' class on sidebar and 'expanded' on main content
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');

        // Save the sidebar's collapsed state in localStorage for persistence across sessions
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
    });

    // Add event listeners to sidebar links to highlight the active link
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove 'active' class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            // Add 'active' class to the clicked link
            link.classList.add('active');
        });
    });

    // Check localStorage to preserve the sidebar state (collapsed or expanded) on page load
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        // If the sidebar was collapsed previously, apply the 'collapsed' class to the sidebar
        sidebar.classList.add('collapsed');
        // Apply the 'expanded' class to the main content to make room for the collapsed sidebar
        mainContent.classList.add('expanded');
    }
});
