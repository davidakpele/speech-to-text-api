// This script handles the real-time polling of the status page.
// The file ID and status are passed from the Jinja2 template via data attributes.
const script = document.currentScript;
const fileId = script.getAttribute('data-file-id');
const jobStatus = script.getAttribute('data-status');

// Only poll if the job is still processing.
if (jobStatus === "processing") {
    const pollInterval = setInterval(() => {
        fetch(`/api/status/${fileId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status !== "processing") {
                    // Stop polling and reload the page to show the completed or error state.
                    clearInterval(pollInterval);
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error("Error fetching status:", error);
                clearInterval(pollInterval); // Stop on error to prevent endless requests.
            });
    }, 3000); // Poll every 3 seconds.
}
