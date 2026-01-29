/**
 * Wikipedia Chain Finder - Frontend Logic
 *
 * This module handles:
 * - Input validation (trim whitespace, check empty fields)
 * - API interaction with the backend
 * - UI state management (loading, results, errors)
 * - Rendering search results as clickable Wikipedia links
 */

(function () {
    'use strict';

    // API endpoint
    const API_BASE_URL = '/api';

    // DOM Elements
    const elements = {
        form: document.getElementById('search-form'),
        startInput: document.getElementById('start-article'),
        endInput: document.getElementById('end-article'),
        submitBtn: document.getElementById('submit-btn'),
        errorContainer: document.getElementById('error-container'),
        errorMessage: document.getElementById('error-message'),
        resultsContainer: document.getElementById('results-container'),
        resultsStats: document.getElementById('results-stats'),
        resultsPath: document.getElementById('results-path'),
    };

    /**
     * Initialize the application
     */
    function init() {
        // Attach event listeners
        elements.form.addEventListener('submit', handleSubmit);

        // Focus the first input on load
        elements.startInput.focus();
    }

    /**
     * Handle form submission
     * @param {Event} event - The submit event
     */
    async function handleSubmit(event) {
        event.preventDefault();

        // Get and trim input values
        const start = elements.startInput.value.trim();
        const end = elements.endInput.value.trim();

        // Client-side validation
        if (!start) {
            showError('Please enter a start article title.');
            elements.startInput.focus();
            return;
        }

        if (!end) {
            showError('Please enter an end article title.');
            elements.endInput.focus();
            return;
        }

        // Hide previous results/errors
        hideError();
        hideResults();

        // Set loading state
        setLoading(true);

        try {
            const result = await findPath(start, end);

            if (result.success) {
                showResults(result);
            } else {
                showError(result.error || 'An error occurred. Please try again.');
            }
        } catch (error) {
            console.error('Search error:', error);
            showError(getErrorMessage(error));
        } finally {
            setLoading(false);
        }
    }

    /**
     * Make API request to find path between articles
     * @param {string} start - Start article title
     * @param {string} end - End article title
     * @returns {Promise<Object>} API response
     */
    async function findPath(start, end) {
        const response = await fetch(`${API_BASE_URL}/find-path`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ start, end }),
        });

        const data = await response.json();

        // If the response is not OK but we got JSON, return it (contains error message)
        if (!response.ok && data.error) {
            return data;
        }

        // If the response is not OK and no error message, throw
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return data;
    }

    /**
     * Set the loading state of the UI
     * @param {boolean} isLoading - Whether the UI should be in loading state
     */
    function setLoading(isLoading) {
        elements.submitBtn.disabled = isLoading;
        elements.startInput.disabled = isLoading;
        elements.endInput.disabled = isLoading;

        if (isLoading) {
            elements.submitBtn.classList.add('loading');
            elements.submitBtn.setAttribute('aria-busy', 'true');
        } else {
            elements.submitBtn.classList.remove('loading');
            elements.submitBtn.removeAttribute('aria-busy');
        }
    }

    /**
     * Show an error message
     * @param {string} message - The error message to display
     */
    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorContainer.hidden = false;
        elements.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Hide the error message
     */
    function hideError() {
        elements.errorContainer.hidden = true;
        elements.errorMessage.textContent = '';
    }

    /**
     * Show the search results
     * @param {Object} result - The search result from the API
     */
    function showResults(result) {
        // Display stats
        const depthText = result.depth === 1 ? '1 step' : `${result.depth} steps`;
        const pagesText = result.pages_explored === 1 ? '1 page' : `${result.pages_explored} pages`;
        elements.resultsStats.textContent = `Found in ${depthText} (${pagesText} explored)`;

        // Build the path display
        elements.resultsPath.innerHTML = '';

        result.path.forEach((article, index) => {
            const pathItem = document.createElement('span');
            pathItem.className = 'path-item';

            // Create the article link
            const link = document.createElement('a');
            link.className = 'path-link';
            link.href = getWikipediaUrl(article);
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = article;
            link.setAttribute('aria-label', `Open ${article} on Wikipedia`);

            pathItem.appendChild(link);

            // Add arrow if not the last item
            if (index < result.path.length - 1) {
                const arrow = document.createElement('span');
                arrow.className = 'path-arrow';
                arrow.textContent = '\u2192'; // Right arrow
                arrow.setAttribute('aria-hidden', 'true');
                pathItem.appendChild(arrow);
            }

            elements.resultsPath.appendChild(pathItem);
        });

        // Show the results container
        elements.resultsContainer.hidden = false;
        elements.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Hide the results section
     */
    function hideResults() {
        elements.resultsContainer.hidden = true;
        elements.resultsStats.textContent = '';
        elements.resultsPath.innerHTML = '';
    }

    /**
     * Get the Wikipedia URL for an article title
     * @param {string} title - The article title
     * @returns {string} The Wikipedia URL
     */
    function getWikipediaUrl(title) {
        // Replace spaces with underscores and encode special characters
        const encodedTitle = encodeURIComponent(title.replace(/ /g, '_'));
        return `https://en.wikipedia.org/wiki/${encodedTitle}`;
    }

    /**
     * Get a user-friendly error message from an error
     * @param {Error} error - The error object
     * @returns {string} A user-friendly error message
     */
    function getErrorMessage(error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            return 'Unable to connect to the server. Please check your internet connection and try again.';
        }

        if (error.message.includes('HTTP error: 429')) {
            return 'Wikipedia rate limit reached. Please wait a minute and try again.';
        }

        if (error.message.includes('HTTP error')) {
            return 'The server encountered an error. Please try again later.';
        }

        return 'An unexpected error occurred. Please try again.';
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
