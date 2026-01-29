# Wikipedia Chain Finder

A web application that finds the shortest path between two Wikipedia articles using bidirectional search.

## Overview

Wikipedia Chain Finder helps you discover how any two Wikipedia articles are connected through hyperlinks. Enter a start article and an end article, and the application will find the shortest chain of links connecting them.

For example: **Python (programming language)** → **Integrated development environment** → **Computer science**

## Features

- Bidirectional search algorithm for efficient path finding
- Real-time Wikipedia API integration
- Clean, responsive user interface
- Clickable article links in results
- Handles redirects and article normalization automatically

## Project Structure

```
project/
├── backend/
│   ├── app.py                    # Flask application and REST API
│   ├── wikipedia_client.py       # Wikipedia API client
│   ├── search.py                 # Bidirectional search algorithm
│   ├── requirements.txt          # Python dependencies
│   ├── test_wikipedia_client.py  # Wikipedia client tests
│   ├── test_search.py            # Search algorithm tests
│   └── test_app.py               # API endpoint tests
├── frontend/
│   ├── index.html                # Main HTML page
│   ├── style.css                 # Styles
│   └── script.js                 # Frontend logic
├── specs.md                      # Project specification
├── plan.md                       # Implementation plan
└── README.md                     # This file
```

## Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone the repository and navigate to the project directory.

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the application:
   ```bash
   python backend/app.py
   ```

4. Open http://localhost:5000 in your browser.

## Usage

1. Enter the title of a Wikipedia article in the "Start Article" field (e.g., "Albert Einstein")
2. Enter the title of another Wikipedia article in the "End Article" field (e.g., "Physics")
3. Click "Find Path"
4. The application will display the shortest chain of articles connecting them
5. Click any article in the chain to open it on Wikipedia

### Tips

- Article titles are case-insensitive for the first character
- You can use underscores or spaces in article titles
- Redirects are handled automatically (e.g., "USA" will redirect to "United States")

## API Documentation

### Health Check

Check if the server is running.

- **Endpoint:** `GET /api/health`
- **Response:**
  ```json
  {
    "status": "ok"
  }
  ```

### Find Path

Find the shortest path between two Wikipedia articles.

- **Endpoint:** `POST /api/find-path`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "start": "Start_Article_Title",
    "end": "End_Article_Title"
  }
  ```

- **Success Response (200):**
  ```json
  {
    "success": true,
    "path": ["Start Article", "Intermediate Article", "End Article"],
    "depth": 2,
    "pages_explored": 150
  }
  ```

- **Error Response (400 - Validation Error):**
  ```json
  {
    "success": false,
    "error": "Missing required field: 'start'"
  }
  ```

- **Error Response (404 - Article Not Found):**
  ```json
  {
    "success": false,
    "error": "Start article not found: 'NonExistentArticle'"
  }
  ```

- **Error Response (404 - No Path Found):**
  ```json
  {
    "success": false,
    "error": "No path found between 'Article A' and 'Article B' within the search depth limit"
  }
  ```

## Algorithm

The application uses a **bidirectional search** algorithm:

1. Start searching from both the start article and the end article simultaneously
2. Expand the frontier of visited articles in alternating directions
3. When the two search frontiers meet, reconstruct the path
4. The maximum search depth is 3 levels in each direction (max path length of 7)

This approach is more efficient than a single-direction search because it explores fewer articles to find the shortest path.

## Running Tests

Run all tests:
```bash
cd backend
python -m unittest discover -v
```

Run specific test files:
```bash
python -m unittest test_wikipedia_client -v
python -m unittest test_search -v
python -m unittest test_app -v
```

## Known Limitations

- **Search Depth:** The maximum path length is 7 articles (3 hops from each direction). Very distantly related articles may not find a path.
- **Search Time:** Complex searches may take 30-60 seconds due to Wikipedia API rate limits.
- **English Wikipedia Only:** Currently only searches the English Wikipedia.
- **Article Links:** Only follows links in the main article namespace (excludes categories, files, templates, etc.).

## Technology Stack

- **Backend:** Python, Flask, Flask-CORS
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **External API:** Wikipedia MediaWiki API

## Development Status

- [x] Phase 1: Project Setup
- [x] Phase 2: Wikipedia Client
- [x] Phase 3: Search Algorithm
- [x] Phase 4: Flask Backend API
- [x] Phase 5: Frontend Implementation
- [x] Phase 6: Integration and Serving
- [ ] Phase 7: End-to-End Testing
- [ ] Phase 8: Polish and Documentation
