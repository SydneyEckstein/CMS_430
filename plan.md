# Wikipedia Chain Finder - Implementation Plan

## Overview

This document outlines a phased approach to building the Wikipedia Chain Finder application. Each phase builds upon the previous one, with clear testing criteria that must pass before proceeding.

---

## Phase 1: Project Setup and Structure

**Goal**: Establish the project foundation with proper file structure and dependencies.

### Steps

1.1. Create the directory structure:
```
project/
├── backend/
│   ├── app.py
│   ├── wikipedia_client.py
│   ├── search.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

1.2. Create `backend/requirements.txt` with dependencies:
- Flask
- requests
- flask-cors (for CORS support)

1.3. Create placeholder files for all modules with basic docstrings describing their purpose.

1.4. Set up a basic Flask app in `app.py` with a health check endpoint (`GET /api/health`).

1.5. Verify Flask runs and responds to the health check.

### Testing Criteria

- [ ] All directories and files exist
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `python backend/app.py` starts the server on localhost:5000
- [ ] `GET /api/health` returns `{"status": "ok"}`

---

## Phase 2: Wikipedia Client Module

**Goal**: Build a robust client for interacting with the Wikipedia API.

### Steps

2.1. **Implement article title normalization function**
- Replace spaces with underscores
- Handle first-character case insensitivity
- URL encode special characters

2.2. **Implement article validation function** (`validate_article`)
- Use Wikipedia API to check if an article exists
- Handle redirects transparently (follow them and return the canonical title)
- Return the normalized/canonical title if valid, raise exception if not found

2.3. **Implement link retrieval function** (`get_article_links`)
- Fetch all outgoing links from an article
- Filter to namespace 0 only (main articles)
- Exclude special pages, user pages, Wikipedia administrative pages, talk pages, file/image pages, category pages, and template pages
- Handle pagination (Wikipedia API returns links in batches)
- Return a list of normalized article titles

2.4. **Implement rate limiting/error handling**
- Add retry logic for transient failures
- Handle HTTP errors gracefully
- Add appropriate User-Agent header (required by Wikipedia API)

2.5. **Create unit tests for the Wikipedia client**
- Test title normalization with various inputs
- Test article validation with valid/invalid articles
- Test redirect handling
- Test link retrieval returns expected format
- Test namespace filtering

### Testing Criteria

- [ ] `normalize_title("python programming")` returns `"Python_programming"`
- [ ] `normalize_title("PYTHON")` returns `"Python"` (first char case handled)
- [ ] `validate_article("Python_(programming_language)")` returns the canonical title
- [ ] `validate_article("ThisArticleDoesNotExist12345")` raises appropriate exception
- [ ] `validate_article("Python")` follows redirect if it redirects somewhere
- [ ] `get_article_links("Python_(programming_language)")` returns a non-empty list
- [ ] All returned links are in namespace 0 (no "Category:", "File:", etc.)
- [ ] API calls include proper User-Agent header

---

## Phase 3: Bidirectional Iterative Deepening Search Algorithm

**Goal**: Implement the core search algorithm that finds the shortest path between two articles.

### Steps

3.1. **Create data structures**
- Forward and backward visited dictionaries (page → parent mapping)
- Forward and backward frontier sets
- Depth tracking variables

3.2. **Implement the main search function** (`find_path`)
- Accept start and end article titles
- Handle edge case: start == end (return immediately)
- Validate both articles exist using Wikipedia client
- Initialize data structures

3.3. **Implement frontier expansion**
- Create `expand_frontier` helper function
- For each page in current frontier, fetch links via Wikipedia client
- Add unvisited links to new frontier
- Record parent relationships

3.4. **Implement intersection detection**
- After each frontier expansion, check for overlap between forward_visited and backward_visited
- Return the meeting point if found

3.5. **Implement path reconstruction**
- Given a meeting point, trace back to start via forward_visited
- Trace back to end via backward_visited
- Combine paths correctly (avoid duplicate meeting point)

3.6. **Implement the main loop**
- Alternate between forward and backward expansion
- Enforce maximum depth limit (3 per direction)
- Track pages explored for statistics

3.7. **Create unit tests with mocked Wikipedia client**
- Test trivial case (start == end)
- Test direct link (depth 1)
- Test two-step path (depth 2)
- Test path not found within limit
- Test path reconstruction correctness

### Testing Criteria

- [ ] `find_path("A", "A")` returns `["A"]` immediately
- [ ] With mocked links A→B, search from A to B returns `["A", "B"]`
- [ ] With mocked links A→B→C, search from A to C returns `["A", "B", "C"]`
- [ ] Path reconstruction correctly combines forward and backward paths
- [ ] Search respects maximum depth limit (returns error if path too long)
- [ ] `pages_explored` count is accurate
- [ ] Search handles case where no path exists

---

## Phase 4: Flask Backend API

**Goal**: Create the REST API endpoint that ties together the Wikipedia client and search algorithm.

### Steps

4.1. **Implement request validation**
- Parse JSON body
- Validate required fields (start, end)
- Trim whitespace from inputs
- Check for empty fields
- Check start != end (or handle as valid edge case)

4.2. **Implement the `/api/find-path` endpoint**
- Accept POST requests with JSON body
- Call search algorithm with validated inputs
- Format successful response with path, depth, and pages_explored
- Return appropriate HTTP status codes

4.3. **Implement error handling**
- Catch article not found errors → 404
- Catch validation errors → 400
- Catch search depth exceeded → 404 with appropriate message
- Catch unexpected errors → 500
- All errors return consistent JSON format

4.4. **Enable CORS**
- Configure Flask-CORS for cross-origin requests
- Allow requests from localhost during development

4.5. **Add request logging**
- Log incoming requests
- Log search results (success/failure, time taken)

4.6. **Create API tests**
- Test successful path finding
- Test validation errors (missing fields, empty fields)
- Test article not found errors
- Test error response format

### Testing Criteria

- [ ] `POST /api/find-path` with valid articles returns 200 and path
- [ ] Response includes `success`, `path`, `depth`, and `pages_explored` fields
- [ ] Missing `start` or `end` field returns 400 with error message
- [ ] Empty article title returns 400 with error message
- [ ] Non-existent start article returns 404 with "Start article not found"
- [ ] Non-existent end article returns 404 with "End article not found"
- [ ] Same start and end returns 200 with single-element path
- [ ] CORS headers are present in responses

---

## Phase 5: Frontend Implementation

**Goal**: Build a clean, functional user interface matching the design specifications.

### Steps

5.1. **Create HTML structure** (`index.html`)
- Header with application title
- Input section with two labeled text fields
- Submit button
- Results section (hidden initially)
- Loading spinner (hidden initially)
- Error message area (hidden initially)

5.2. **Implement CSS styling** (`style.css`)
- Apply specified color scheme:
  - Background: #F5F5F4
  - Text: #2C2C2C
  - Accent: warm brown/copper for interactive elements
  - Borders: #E5E5E5
- Set font stack (Inter, SF Pro, Segoe UI, system fonts)
- Create centered, clean layout with generous whitespace
- Style input fields, button, and results
- Style loading spinner (CSS animation)
- Style error messages (clear but not harsh)
- Ensure responsive design for different screen sizes

5.3. **Implement JavaScript logic** (`script.js`)
- Input validation:
  - Trim whitespace
  - Check for empty fields
  - Disable submit during search
- API interaction:
  - Make POST request to `/api/find-path`
  - Handle loading state (show spinner, disable button)
  - Parse JSON response
- Results display:
  - On success: render clickable article chain with arrows
  - Each article links to `https://en.wikipedia.org/wiki/{title}`
  - On error: display error message
- Reset UI state appropriately after each search

5.4. **Add accessibility features**
- Proper label associations
- Keyboard navigation support
- ARIA attributes where appropriate
- Focus management

5.5. **Create manual UI tests checklist**
- Test all UI states render correctly
- Test input validation feedback
- Test loading state appearance
- Test successful result display
- Test error message display
- Test links open correct Wikipedia pages

### Testing Criteria

- [ ] Page loads without JavaScript errors
- [ ] Input fields have proper labels and placeholders
- [ ] Empty field submission shows validation error (client-side)
- [ ] Submit button disables during search
- [ ] Loading spinner appears during API call
- [ ] Successful search displays article chain with arrows
- [ ] Each article in chain is a clickable link to Wikipedia
- [ ] Error responses display user-friendly messages
- [ ] UI resets properly for new searches
- [ ] Layout looks correct on desktop and mobile viewports
- [ ] Color scheme matches specification

---

## Phase 6: Integration and Serving

**Goal**: Integrate frontend and backend, enable serving the complete application.

### Steps

6.1. **Configure Flask to serve static files**
- Serve `index.html` at root route `/`
- Serve CSS and JS as static files
- Ensure paths work correctly

6.2. **Test full application flow**
- Start Flask server
- Load frontend in browser
- Perform searches and verify results

6.3. **Add comprehensive error handling**
- Handle network errors in frontend
- Handle timeout scenarios
- Add user feedback for long-running searches

6.4. **Create README.md**
- Project description
- Setup instructions
- How to run the application
- API documentation
- Known limitations

### Testing Criteria

- [ ] `python backend/app.py` serves the complete application
- [ ] Frontend loads at `http://localhost:5000/`
- [ ] API calls from frontend reach backend correctly
- [ ] No CORS errors in browser console
- [ ] Application handles network errors gracefully

---

## Phase 7: End-to-End Testing

**Goal**: Verify the complete application works with real Wikipedia data.

### Steps

7.1. **Test with known article pairs**
- Test: "Python (programming language)" → "Computer science" (should find path)
- Test: "Albert Einstein" → "Physics" (should find path)
- Test: "United States" → "George Washington" (should find path)
- Test: Same article for start and end (should return single element)

7.2. **Test edge cases**
- Very long article titles
- Articles with special characters
- Article titles that are redirects
- Recently created/obscure articles

7.3. **Test error scenarios**
- Non-existent start article
- Non-existent end article
- Both articles non-existent
- Articles with no path within depth limit (if findable)

7.4. **Performance testing**
- Measure search time for typical queries
- Verify searches complete within 30-60 second target
- Identify any performance bottlenecks

7.5. **Browser compatibility testing**
- Test in Chrome
- Test in Firefox
- Test in Safari (if available)
- Test in Edge

### Testing Criteria

- [ ] At least 3 different article pairs successfully find paths
- [ ] Paths are valid (each link actually exists on the previous article)
- [ ] Special character handling works correctly
- [ ] Redirect handling works transparently
- [ ] All error cases show appropriate messages
- [ ] Searches complete within 60 seconds for typical pairs
- [ ] Application works in all major browsers

---

## Phase 8: Polish and Documentation

**Goal**: Final refinements and documentation.

### Steps

8.1. **Code cleanup**
- Remove debug statements
- Ensure consistent code style
- Add/update docstrings
- Remove unused imports

8.2. **Improve user experience**
- Add brief instructions text on the page
- Improve error message clarity
- Add example article suggestions

8.3. **Finalize documentation**
- Complete README.md with all sections
- Add inline code comments where helpful
- Document any known limitations or issues

8.4. **Final testing pass**
- Complete end-to-end test of all features
- Verify all testing criteria from previous phases still pass

### Testing Criteria

- [ ] Code passes linting (if linter configured)
- [ ] All functions have docstrings
- [ ] README contains setup and usage instructions
- [ ] No console errors or warnings in normal operation
- [ ] Application meets all success criteria from specification

---

## Summary: Dependency Graph

```
Phase 1: Project Setup
    ↓
Phase 2: Wikipedia Client
    ↓
Phase 3: Search Algorithm (depends on Phase 2)
    ↓
Phase 4: Flask Backend API (depends on Phase 3)
    ↓
Phase 5: Frontend (can start after Phase 4 API is defined)
    ↓
Phase 6: Integration (depends on Phases 4 & 5)
    ↓
Phase 7: End-to-End Testing (depends on Phase 6)
    ↓
Phase 8: Polish and Documentation
```

---

## Estimated Complexity by Phase

| Phase | Description | Relative Complexity |
|-------|-------------|---------------------|
| 1 | Project Setup | Low |
| 2 | Wikipedia Client | Medium |
| 3 | Search Algorithm | High |
| 4 | Flask Backend | Medium |
| 5 | Frontend | Medium |
| 6 | Integration | Low |
| 7 | E2E Testing | Medium |
| 8 | Polish | Low |

---

## Risk Areas and Mitigations

### Risk 1: Wikipedia API Rate Limiting
- **Mitigation**: Implement proper User-Agent, add delays if needed, handle 429 responses

### Risk 2: Search Performance
- **Mitigation**: Depth limit of 3 per direction caps worst-case; consider early termination if frontier grows too large

### Risk 3: Article Link Volume
- **Mitigation**: Some articles have thousands of links; ensure pagination handling is robust

### Risk 4: Redirect Chains
- **Mitigation**: Follow redirects but cap redirect depth to prevent infinite loops

### Risk 5: Character Encoding Issues
- **Mitigation**: Properly URL encode/decode all article titles; test with special characters

---

## Success Criteria Checklist (from Specification)

- [ ] User can input two Wikipedia article titles
- [ ] Application finds a path between them (if one exists within depth limit)
- [ ] Results are displayed as clickable Wikipedia links
- [ ] Clear error messages for common failure cases
- [ ] Clean, minimal UI matching the specified aesthetic
- [ ] Search completes within 30-60 seconds for typical article pairs
