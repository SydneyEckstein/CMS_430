# Wikipedia Chain Finder - Project Specification

## Project Overview
A web application that finds the shortest path between two Wikipedia articles using bidirectional iterative deepening search. The application consists of a simple frontend (HTML/CSS/vanilla JavaScript) and a Python Flask backend.

## Frontend Specification

### Technology
HTML, CSS, vanilla JavaScript

### Design Aesthetic
- **Font family**: Use a clean sans-serif stack similar to Claude's interface (e.g., system fonts or "Inter", "SF Pro", "Segoe UI")
- **Color scheme**: Neutral, minimalist palette
  - Background: Light warm off-white (#F5F5F4 or similar)
  - Text: Dark gray/charcoal (#2C2C2C)
  - Accent: Subtle warm brown/copper tones for interactive elements
  - Borders: Light gray (#E5E5E5)
- **Layout**: Centered, clean, generous whitespace

### UI Components
1. **Header**: Simple title "Wikipedia Chain Finder" or similar
2. **Input Section**:
   - Two text input fields:
     - Label: "Start Article"
     - Label: "End Article"
     - Placeholder text with examples (e.g., "Enter Wikipedia article title")
   - Submit button ("Find Path" or similar)
3. **Results Section**:
   - Loading spinner (shown during search)
   - Results display area:
     - On success: Display chain as clickable links to Wikipedia articles
     - Format: "Article 1 → Article 2 → Article 3 → ..." 
     - Each article name should be a hyperlink to the actual Wikipedia page
   - Error messages (styled clearly but not harshly)
4. **Optional**: Brief instructions or description of what the tool does

### Behavior
- On submit: Show loading spinner, disable submit button, make API call
- On success: Hide spinner, display article chain with clickable Wikipedia links
- On error: Hide spinner, display error message, re-enable submit button
- Input validation: Trim whitespace from inputs, check for empty fields before submitting

## Backend Specification

### Technology
Python Flask

### API Endpoint
- **Route**: `POST /api/find-path`
- **Request Body** (JSON):
```json
  {
    "start": "Article_Title",
    "end": "Article_Title"
  }
```
- **Response** (JSON):
  - Success (200):
```json
    {
      "success": true,
      "path": ["Article1", "Article2", "Article3", ...],
      "depth": 3,
      "pages_explored": 150
    }
```
  - Error (400/404/500):
```json
    {
      "success": false,
      "error": "Descriptive error message"
    }
```

### Error Messages (examples)
- "Start article not found"
- "End article not found"
- "No path exists within depth limit"
- "Invalid article title"
- "Start and end articles are the same"

## Wikipedia API Integration

### API
Wikimedia REST API or MediaWiki Action API

### Required Operations
1. **Article Validation**: Check if an article exists
2. **Link Retrieval**: Get all outgoing links from an article

### Link Filtering Rules
- Only include links in namespace 0 (main article namespace)
- Exclude:
  - Special pages (Special:*)
  - User pages (User:*)
  - Wikipedia administrative pages (Wikipedia:*)
  - Talk pages (*_talk:*)
  - File/Image pages (File:*, Image:*)
  - Category pages (Category:*)
  - Template pages (Template:*)
- Include all links from the article content (main text, infoboxes, "See also", etc.)
- Handle redirects by following them transparently

### Article Title Normalization
- Wikipedia treats the first character as case-insensitive (e.g., "python" → "Python")
- Preserve casing for the rest of the title
- Replace spaces with underscores when making API calls
- Handle URL encoding as needed

## Algorithm: Bidirectional Iterative Deepening Search

### Core Strategy
1. Initialize two searches: forward (from start) and backward (from end)
2. Alternate between expanding forward and backward searches
3. Increase depth limit with each iteration: depth 0, then 1, then 2, etc.
4. Check for intersection after completing each depth level
5. Maximum depth: 3 per direction (total chain length ≤ 7 articles)

### Implementation Details

#### Data Structures
- Forward frontier: Set of pages reachable from start at current depth
- Backward frontier: Set of pages reachable from end at current depth
- Forward visited: Dict mapping each visited page to its parent in the forward search
- Backward visited: Dict mapping each visited page to its parent in the backward search
- Forward depth: Current depth of forward search
- Backward depth: Current depth of backward search

#### Algorithm Flow
```
1. If start == end: return [start]

2. Validate that start and end articles exist

3. Initialize:
   - forward_visited = {start: None}
   - backward_visited = {end: None}
   - forward_frontier = {start}
   - backward_frontier = {end}
   - current_depth = 0

4. While current_depth <= 3:
   
   a. Expand forward frontier:
      - For each page in forward_frontier:
        - Fetch links from page
        - Add unvisited links to new_forward_frontier
        - Record parent in forward_visited
      - Check for intersection with backward_visited
      - If found: reconstruct and return path
      - forward_frontier = new_forward_frontier
   
   b. Expand backward frontier:
      - For each page in backward_frontier:
        - Fetch links from page
        - Add unvisited links to new_backward_frontier
        - Record parent in backward_visited
      - Check for intersection with forward_visited
      - If found: reconstruct and return path
      - backward_frontier = new_backward_frontier
   
   c. Increment current_depth

5. If no path found: return error "No path exists within depth limit"
```

#### Path Reconstruction
When a page P is found in both forward_visited and backward_visited:
1. Trace backward from P to start using forward_visited parents
2. Trace backward from P to end using backward_visited parents
3. Reverse the forward path
4. Concatenate: forward_path + [P] + reversed(backward_path)
5. Remove duplicate P if it appears twice

#### Note on "Backward" Search
The backward search from the goal still follows forward links (since we can't easily get "what pages link to this page"). It's "backward" in the sense that it starts from the goal and expands outward, meeting the forward search in the middle.

## Technical Requirements

### Python Dependencies
- Flask
- requests (for Wikipedia API calls)
- Any other standard library modules needed

### Constraints
- **No Caching**: First version should not implement any caching of Wikipedia pages or search results
- **Single-threaded**: No need for multi-threading or parallel processing
- **CORS**: Enable CORS if frontend and backend are served separately, or serve frontend from Flask

## File Structure
```
project/
├── backend/
│   ├── app.py              # Flask application and API endpoint
│   ├── wikipedia_client.py # Wikipedia API interaction
│   ├── search.py           # BIDS algorithm implementation
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── style.css           # Styling
│   └── script.js           # JavaScript logic
└── README.md               # Project documentation
```

## Deployment Considerations
- Flask app should be runnable with `python app.py` or `flask run`
- Frontend can be served by Flask or as static files
- Default to running on localhost:5000 or similar

## Success Criteria
1. User can input two Wikipedia article titles
2. Application finds a path between them (if one exists within depth limit)
3. Results are displayed as clickable Wikipedia links
4. Clear error messages for common failure cases
5. Clean, minimal UI matching the specified aesthetic
6. Search completes within 30-60 seconds for typical article pairs
