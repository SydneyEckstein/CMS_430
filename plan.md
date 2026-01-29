# Wikipedia Chain Finder - Implementation Plan

## Overview

This document outlines a phased approach to building the Wikipedia Chain Finder application with SQLite caching support. Each phase builds upon the previous one, with clear testing criteria that must pass before proceeding.

---

## Phase 1: Project Setup and Structure

**Goal**: Establish the project foundation with proper file structure and dependencies.

### Steps

1.1. Create the directory structure:
```
project/
├── backend/
│   ├── app.py
│   ├── db.py                 # NEW: Database/caching module
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

- [ ] All directories and files exist (including `db.py`)
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `python backend/app.py` starts the server on localhost:5000
- [ ] `GET /api/health` returns `{"status": "ok"}`

### Expected Outcomes

- All project files created and in place
- Flask server starts without errors
- Health check endpoint responds correctly

---

## Phase 2: Database Module (SQLite Cache)

**Goal**: Implement the SQLite caching system for storing Wikipedia article links. This module must be completed first since the Wikipedia client depends on it.

### Steps

2.1. **Design the database schema**
- Table: `article_links`
  - `article_title` (TEXT, PRIMARY KEY): The normalized Wikipedia article title
  - `links` (TEXT): JSON-serialized list of outgoing links
  - `cached_at` (TIMESTAMP): When the links were cached
- Table: `cache_metadata` (optional, for stats)
  - `key` (TEXT, PRIMARY KEY)
  - `value` (TEXT)

2.2. **Implement database initialization** (`init_db`)
- Create SQLite database file (`cache.db`) in the backend directory
- Create tables if they don't exist
- Handle database connection errors gracefully

2.3. **Implement cache storage function** (`cache_article_links`)
- Accept article title and list of links
- Serialize links to JSON
- Insert or replace existing entry with current timestamp
- Handle database write errors

2.4. **Implement cache retrieval function** (`get_cached_links`)
- Accept article title
- Query database for cached links
- Check if cache entry is expired (older than 30 days)
- Return `None` if not found or expired
- Return deserialized list of links if valid cache hit
- Delete expired entries when encountered

2.5. **Implement cache clearing function** (`clear_cache`)
- Accept optional article title parameter
- If title provided: delete specific entry
- If no title: delete all entries (full cache clear)
- Return number of entries deleted

2.6. **Implement cache statistics function** (`get_cache_stats`)
- Return dictionary with:
  - `total_articles`: Number of cached articles
  - `total_links`: Total number of links stored across all articles
  - `oldest_entry`: Timestamp of oldest cache entry
  - `newest_entry`: Timestamp of newest cache entry
  - `cache_size_bytes`: Size of the database file
  - `expired_count`: Number of entries older than 30 days

2.7. **Implement cache expiration cleanup** (`cleanup_expired`)
- Delete all entries older than 30 days
- Return number of entries deleted
- Can be called manually or automatically

2.8. **Create unit tests for the database module** (`test_db.py`)
- Test database initialization creates file and tables
- Test storing and retrieving links
- Test cache expiration logic
- Test cache clearing (specific and full)
- Test statistics accuracy

### Testing Criteria

- [ ] `init_db()` creates `cache.db` file in backend directory
- [ ] `cache_article_links("Python", ["Link1", "Link2"])` stores data successfully
- [ ] `get_cached_links("Python")` returns `["Link1", "Link2"]`
- [ ] `get_cached_links("NonExistent")` returns `None`
- [ ] Cache entries older than 30 days return `None` and are deleted
- [ ] `clear_cache("Python")` removes only that article's cache
- [ ] `clear_cache()` removes all cached entries
- [ ] `get_cache_stats()` returns accurate statistics
- [ ] Database handles concurrent access without corruption

### Expected Outcomes

- `cache.db` file is created on first run
- Links can be stored and retrieved reliably
- Expired entries (>30 days) are not returned
- Cache statistics reflect actual database state
- All unit tests pass

---

## Phase 3: Wikipedia Client Module (with Cache Integration)

**Goal**: Build a robust client for interacting with the Wikipedia API that uses the cache from Phase 2.

### Steps

3.1. **Implement article title normalization function**
- Replace spaces with underscores
- Handle first-character case insensitivity
- URL encode special characters

3.2. **Implement article validation function** (`validate_article`)
- Use Wikipedia API to check if an article exists
- Handle redirects transparently (follow them and return the canonical title)
- Return the normalized/canonical title if valid, raise exception if not found

3.3. **Implement link retrieval function with caching** (`get_article_links`)
- **First**: Check cache for existing links using `get_cached_links()`
- **If cache hit**: Return cached links immediately (no API call)
- **If cache miss**:
  - Fetch all outgoing links from Wikipedia API
  - Filter to namespace 0 only (main articles)
  - Exclude special pages, user pages, Wikipedia administrative pages, talk pages, file/image pages, category pages, and template pages
  - Handle pagination (Wikipedia API returns links in batches)
  - Store results in cache using `cache_article_links()`
  - Return list of normalized article titles
- Track and return cache hit/miss status for logging

3.4. **Implement rate limiting/error handling**
- Add retry logic for transient failures
- Handle HTTP errors gracefully
- Add appropriate User-Agent header (required by Wikipedia API)

3.5. **Create unit tests for the Wikipedia client** (`test_wikipedia_client.py`)
- Test title normalization with various inputs
- Test article validation with valid/invalid articles
- Test redirect handling
- Test link retrieval returns expected format
- Test namespace filtering
- Test cache integration (hit and miss scenarios)

### Testing Criteria

- [ ] `normalize_title("python programming")` returns `"Python_programming"`
- [ ] `normalize_title("PYTHON")` returns `"Python"` (first char case handled)
- [ ] `validate_article("Python_(programming_language)")` returns the canonical title
- [ ] `validate_article("ThisArticleDoesNotExist12345")` raises appropriate exception
- [ ] `validate_article("Python")` follows redirect if it redirects somewhere
- [ ] `get_article_links("Python_(programming_language)")` returns a non-empty list
- [ ] All returned links are in namespace 0 (no "Category:", "File:", etc.)
- [ ] API calls include proper User-Agent header
- [ ] **First call** to `get_article_links()` makes API request and caches result
- [ ] **Second call** to same article returns cached data without API call
- [ ] Cache miss is logged/trackable
- [ ] Cache hit is logged/trackable

### Expected Outcomes

- First link retrieval for an article makes Wikipedia API call
- Second link retrieval for same article uses cache (no API call)
- Cache entries appear in `cache.db`
- All unit tests pass

---

## Phase 4: Bidirectional Iterative Deepening Search Algorithm

**Goal**: Implement the core search algorithm that finds the shortest path between two articles.

### Steps

4.1. **Create data structures**
- Forward and backward visited dictionaries (page → parent mapping)
- Forward and backward frontier sets
- Depth tracking variables

4.2. **Implement the main search function** (`find_path`)
- Accept start and end article titles
- Handle edge case: start == end (return immediately)
- Validate both articles exist using Wikipedia client
- Initialize data structures

4.3. **Implement frontier expansion**
- Create `expand_frontier` helper function
- For each page in current frontier, fetch links via Wikipedia client (which uses cache)
- Add unvisited links to new frontier
- Record parent relationships

4.4. **Implement intersection detection**
- After each frontier expansion, check for overlap between forward_visited and backward_visited
- Return the meeting point if found

4.5. **Implement path reconstruction**
- Given a meeting point, trace back to start via forward_visited
- Trace back to end via backward_visited
- Combine paths correctly (avoid duplicate meeting point)

4.6. **Implement the main loop**
- Alternate between forward and backward expansion
- Enforce maximum depth limit (3 per direction)
- Track pages explored for statistics
- Track cache hits/misses for statistics

4.7. **Create unit tests with mocked Wikipedia client** (`test_search.py`)
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

### Expected Outcomes

- Search algorithm correctly finds shortest paths
- Algorithm leverages cached links from Wikipedia client
- All unit tests pass

---

## Phase 5: Flask Backend API (with Cache Stats Endpoint)

**Goal**: Create the REST API endpoints including cache statistics and management.

### Steps

5.1. **Implement request validation**
- Parse JSON body
- Validate required fields (start, end)
- Trim whitespace from inputs
- Check for empty fields
- Check start != end (or handle as valid edge case)

5.2. **Implement the `/api/find-path` endpoint**
- Accept POST requests with JSON body
- Call search algorithm with validated inputs
- Format successful response with path, depth, pages_explored, and cache stats
- Return appropriate HTTP status codes
- Response format:
```json
{
  "success": true,
  "path": ["Article1", "Article2", "Article3"],
  "depth": 2,
  "pages_explored": 150,
  "cache_hits": 45,
  "cache_misses": 105
}
```

5.3. **Implement the `/api/cache-stats` endpoint** (NEW)
- Accept GET requests
- Return cache statistics from `get_cache_stats()`
- Response format:
```json
{
  "success": true,
  "stats": {
    "total_articles": 1234,
    "total_links": 567890,
    "oldest_entry": "2024-01-15T10:30:00Z",
    "newest_entry": "2024-02-14T15:45:00Z",
    "cache_size_bytes": 5242880,
    "expired_count": 12
  }
}
```

5.4. **Implement the `/api/cache-clear` endpoint** (NEW)
- Accept POST requests
- Optional body: `{"article": "Article_Title"}` for specific clear
- Clear entire cache if no article specified
- Return number of entries cleared
- Response format:
```json
{
  "success": true,
  "entries_cleared": 1234,
  "message": "Cache cleared successfully"
}
```

5.5. **Implement error handling**
- Catch article not found errors → 404
- Catch validation errors → 400
- Catch search depth exceeded → 404 with appropriate message
- Catch unexpected errors → 500
- All errors return consistent JSON format

5.6. **Enable CORS**
- Configure Flask-CORS for cross-origin requests
- Allow requests from localhost during development

5.7. **Add request logging**
- Log incoming requests
- Log search results (success/failure, time taken, cache hit rate)

5.8. **Create API tests** (`test_app.py`)
- Test successful path finding
- Test validation errors (missing fields, empty fields)
- Test article not found errors
- Test error response format
- Test cache-stats endpoint
- Test cache-clear endpoint

### Testing Criteria

- [ ] `POST /api/find-path` with valid articles returns 200 and path
- [ ] Response includes `success`, `path`, `depth`, `pages_explored`, `cache_hits`, `cache_misses` fields
- [ ] Missing `start` or `end` field returns 400 with error message
- [ ] Empty article title returns 400 with error message
- [ ] Non-existent start article returns 404 with "Start article not found"
- [ ] Non-existent end article returns 404 with "End article not found"
- [ ] Same start and end returns 200 with single-element path
- [ ] CORS headers are present in responses
- [ ] `GET /api/cache-stats` returns valid statistics JSON
- [ ] `POST /api/cache-clear` clears cache and returns count
- [ ] `POST /api/cache-clear` with `{"article": "X"}` clears only that article

### Expected Outcomes

- All API endpoints respond correctly
- Cache statistics endpoint shows accurate data
- Cache clear endpoint successfully clears cache
- All API tests pass

---

## Phase 6: Frontend Implementation (with Cache Stats Display)

**Goal**: Build a clean, functional user interface with optional cache statistics display.

### Steps

6.1. **Create HTML structure** (`index.html`)
- Header with application title
- Input section with two labeled text fields
- Submit button
- Results section (hidden initially)
- Loading spinner (hidden initially)
- Error message area (hidden initially)
- Cache statistics section (collapsible/optional)

6.2. **Implement CSS styling** (`style.css`)
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
- Style cache statistics section
- Ensure responsive design for different screen sizes

6.3. **Implement JavaScript logic** (`script.js`)
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
  - Display cache hit/miss statistics from search
  - Each article links to `https://en.wikipedia.org/wiki/{title}`
  - On error: display error message
- Cache statistics display (optional feature):
  - Fetch and display stats from `/api/cache-stats`
  - Show cache size, article count, etc.
- Reset UI state appropriately after each search

6.4. **Add accessibility features**
- Proper label associations
- Keyboard navigation support
- ARIA attributes where appropriate
- Focus management

6.5. **Create manual UI tests checklist**
- Test all UI states render correctly
- Test input validation feedback
- Test loading state appearance
- Test successful result display
- Test error message display
- Test links open correct Wikipedia pages
- Test cache statistics display

### Testing Criteria

- [ ] Page loads without JavaScript errors
- [ ] Input fields have proper labels and placeholders
- [ ] Empty field submission shows validation error (client-side)
- [ ] Submit button disables during search
- [ ] Loading spinner appears during API call
- [ ] Successful search displays article chain with arrows
- [ ] Each article in chain is a clickable link to Wikipedia
- [ ] Cache hit/miss info is displayed after search
- [ ] Error responses display user-friendly messages
- [ ] UI resets properly for new searches
- [ ] Layout looks correct on desktop and mobile viewports
- [ ] Color scheme matches specification

### Expected Outcomes

- Frontend displays search results with cache statistics
- Users can see how many articles were cached vs fetched
- UI is clean and matches design specifications

---

## Phase 7: Integration and Serving

**Goal**: Integrate frontend and backend, enable serving the complete application.

### Steps

7.1. **Configure Flask to serve static files**
- Serve `index.html` at root route `/`
- Serve CSS and JS as static files
- Ensure paths work correctly

7.2. **Test full application flow**
- Start Flask server
- Load frontend in browser
- Perform searches and verify results

7.3. **Add comprehensive error handling**
- Handle network errors in frontend
- Handle timeout scenarios
- Add user feedback for long-running searches

7.4. **Create README.md**
- Project description
- Setup instructions
- How to run the application
- API documentation (including cache endpoints)
- Known limitations

### Testing Criteria

- [ ] `python backend/app.py` serves the complete application
- [ ] Frontend loads at `http://localhost:5000/`
- [ ] API calls from frontend reach backend correctly
- [ ] No CORS errors in browser console
- [ ] Application handles network errors gracefully
- [ ] Cache database is created on first run

### Expected Outcomes

- Complete application runs from single Flask server
- All components work together seamlessly
- Cache persists between server restarts

---

## Phase 8: Cache-Specific Testing

**Goal**: Comprehensive testing of the SQLite caching system to ensure it works correctly under all conditions.

### Steps

8.1. **Test cache miss (first run)**
- Clear the cache completely
- Run a search between two articles
- Verify:
  - All link fetches result in cache misses
  - Links are stored in cache after fetching
  - `cache.db` file size increases
  - `get_cache_stats()` shows new entries

8.2. **Test cache hit (second run with same search)**
- Run the same search again without clearing cache
- Verify:
  - Search completes significantly faster (target: <5 seconds for cached data)
  - No new Wikipedia API calls are made for cached articles
  - Cache hit count matches expected value
  - `cache.db` file size remains the same

8.3. **Test cache expiration (30-day limit)**
- Manually insert a cache entry with a timestamp older than 30 days
- Attempt to retrieve that entry
- Verify:
  - `get_cached_links()` returns `None` for expired entry
  - Expired entry is deleted from database
  - `get_cache_stats()` shows correct expired count
  - Fresh fetch occurs and new entry is cached

8.4. **Test manual cache clearing**
- Populate cache with multiple entries
- Test clearing specific article: `clear_cache("Python")`
- Verify:
  - Only that article's cache is removed
  - Other entries remain intact
- Test clearing entire cache: `clear_cache()`
- Verify:
  - All entries are removed
  - `cache.db` still exists but tables are empty
  - `get_cache_stats()` shows zero entries

8.5. **Test partial cache hits**
- Cache links for article A but not article B
- Run search that requires both A and B
- Verify:
  - Article A uses cached links (cache hit)
  - Article B fetches from API (cache miss)
  - Article B is then cached for future use
  - Statistics correctly reflect partial hit scenario

8.6. **Performance comparison (cached vs uncached)**
- Clear cache
- Time a search and record duration (uncached)
- Run same search again and time it (cached)
- Verify:
  - Cached search is at least 10x faster
  - For a typical search, cached version completes in <5 seconds
  - Uncached version may take 30-60 seconds

8.7. **Test database integrity**
- Perform multiple concurrent searches (if applicable)
- Verify database is not corrupted
- Verify all entries are valid JSON
- Test recovery after simulated crash (kill process mid-search)

### Testing Criteria

- [ ] First search populates cache correctly
- [ ] Second identical search uses cache (no API calls)
- [ ] Cached search completes in <5 seconds
- [ ] Uncached search takes 30-60 seconds (performance improvement confirmed)
- [ ] Entries older than 30 days are treated as misses
- [ ] Expired entries are automatically deleted
- [ ] `clear_cache()` removes all entries
- [ ] `clear_cache("Article")` removes only that entry
- [ ] Partial cache hits work correctly
- [ ] Cache statistics are accurate after all operations
- [ ] Database handles errors gracefully

### Expected Outcomes

- Cache dramatically speeds up repeated searches (10x or more)
- Cache expiration prevents stale data
- Cache clearing works for both specific and full clear
- Statistics accurately reflect cache state

---

## Phase 9: End-to-End Testing

**Goal**: Verify the complete application works with real Wikipedia data and cache.

### Steps

9.1. **Test with known article pairs**
- Test: "Python (programming language)" → "Computer science" (should find path)
- Test: "Albert Einstein" → "Physics" (should find path)
- Test: "United States" → "George Washington" (should find path)
- Test: Same article for start and end (should return single element)

9.2. **Test edge cases**
- Very long article titles
- Articles with special characters
- Article titles that are redirects
- Recently created/obscure articles

9.3. **Test error scenarios**
- Non-existent start article
- Non-existent end article
- Both articles non-existent
- Articles with no path within depth limit (if findable)

9.4. **Performance testing with cache**
- Run initial search (uncached) - measure time
- Run same search (cached) - measure time
- Verify significant performance improvement
- Run different search that shares some articles with first - verify partial caching

9.5. **Browser compatibility testing**
- Test in Chrome
- Test in Firefox
- Test in Safari (if available)
- Test in Edge

9.6. **Cache persistence testing**
- Run a search to populate cache
- Stop the Flask server
- Restart the Flask server
- Run the same search - verify it uses cached data

### Testing Criteria

- [ ] At least 3 different article pairs successfully find paths
- [ ] Paths are valid (each link actually exists on the previous article)
- [ ] Special character handling works correctly
- [ ] Redirect handling works transparently
- [ ] All error cases show appropriate messages
- [ ] Initial searches complete within 60 seconds
- [ ] Cached searches complete within 5 seconds
- [ ] Application works in all major browsers
- [ ] Cache persists across server restarts

### Expected Outcomes

- Application works correctly with real Wikipedia data
- Cache provides significant performance improvement
- All edge cases handled gracefully

---

## Phase 10: Polish and Documentation

**Goal**: Final refinements and documentation.

### Steps

10.1. **Code cleanup**
- Remove debug statements
- Ensure consistent code style
- Add/update docstrings
- Remove unused imports

10.2. **Improve user experience**
- Add brief instructions text on the page
- Improve error message clarity
- Add example article suggestions
- Display cache statistics in a user-friendly way

10.3. **Finalize documentation**
- Complete README.md with all sections
- Document cache configuration options
- Document API endpoints including cache endpoints
- Add inline code comments where helpful
- Document any known limitations or issues

10.4. **Final testing pass**
- Complete end-to-end test of all features
- Verify all testing criteria from previous phases still pass
- Verify cache works correctly in all scenarios

### Testing Criteria

- [ ] Code passes linting (if linter configured)
- [ ] All functions have docstrings
- [ ] README contains setup and usage instructions
- [ ] README documents cache functionality
- [ ] No console errors or warnings in normal operation
- [ ] Application meets all success criteria from specification

### Expected Outcomes

- Code is clean and well-documented
- README provides complete usage instructions
- All features work correctly

---

## Summary: Dependency Graph

```
Phase 1: Project Setup
    ↓
Phase 2: Database Module (SQLite Cache) ← NEW: Must be first
    ↓
Phase 3: Wikipedia Client (with Cache Integration) ← MODIFIED: Uses cache
    ↓
Phase 4: Search Algorithm (depends on Phase 3)
    ↓
Phase 5: Flask Backend API (with Cache Stats Endpoint) ← MODIFIED: New endpoints
    ↓
Phase 6: Frontend (with Cache Stats Display) ← MODIFIED: Shows cache info
    ↓
Phase 7: Integration (depends on Phases 5 & 6)
    ↓
Phase 8: Cache-Specific Testing ← NEW: Dedicated cache testing
    ↓
Phase 9: End-to-End Testing (depends on Phase 7)
    ↓
Phase 10: Polish and Documentation
```

---

## Estimated Complexity by Phase

| Phase | Description | Relative Complexity |
|-------|-------------|---------------------|
| 1 | Project Setup | Low |
| 2 | Database Module (Cache) | Medium |
| 3 | Wikipedia Client (with Cache) | Medium |
| 4 | Search Algorithm | High |
| 5 | Flask Backend (with Cache Endpoints) | Medium |
| 6 | Frontend (with Cache Display) | Medium |
| 7 | Integration | Low |
| 8 | Cache-Specific Testing | Medium |
| 9 | E2E Testing | Medium |
| 10 | Polish | Low |

---

## Risk Areas and Mitigations

### Risk 1: Wikipedia API Rate Limiting
- **Mitigation**: Implement proper User-Agent, add delays if needed, handle 429 responses
- **Cache Benefit**: Caching significantly reduces API calls, lowering rate limit risk

### Risk 2: Search Performance
- **Mitigation**: Depth limit of 3 per direction caps worst-case; cache provides major speedup for repeated searches

### Risk 3: Article Link Volume
- **Mitigation**: Some articles have thousands of links; ensure pagination handling is robust; cache stores complete link lists

### Risk 4: Redirect Chains
- **Mitigation**: Follow redirects but cap redirect depth to prevent infinite loops

### Risk 5: Character Encoding Issues
- **Mitigation**: Properly URL encode/decode all article titles; test with special characters

### Risk 6: Cache Database Corruption
- **Mitigation**: Use SQLite transactions; implement database integrity checks; handle concurrent access properly

### Risk 7: Stale Cache Data
- **Mitigation**: 30-day expiration ensures reasonably fresh data; manual clear option available

---

## Cache Configuration Constants

The following constants should be defined in `db.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `CACHE_DB_PATH` | `cache.db` | SQLite database file path |
| `CACHE_EXPIRATION_DAYS` | `30` | Number of days before cache entries expire |
| `TABLE_ARTICLE_LINKS` | `article_links` | Table name for cached links |

---

## Final Validation Checklist

### Core Functionality
- [ ] User can input two Wikipedia article titles
- [ ] Application finds a path between them (if one exists within depth limit)
- [ ] Results are displayed as clickable Wikipedia links
- [ ] Clear error messages for common failure cases
- [ ] Clean, minimal UI matching the specified aesthetic

### Cache Functionality
- [ ] Cache dramatically speeds up repeated searches (10x improvement)
- [ ] Cache expiration works correctly (30 days)
- [ ] Manual cache clearing works (specific and full)
- [ ] Cache statistics are accurate and accessible via API
- [ ] Cache persists across server restarts
- [ ] Partial cache hits handled correctly

### Performance
- [ ] Initial search completes within 60 seconds for typical article pairs
- [ ] Cached search completes within 5 seconds
- [ ] Cache size remains reasonable (monitored via stats)
