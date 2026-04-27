# Search Architecture Part 4: Search UX

> Autocomplete, faceted search, and results display patterns

**Series:** Search Architecture
**Previous:** [Part 3: Relevance & Ranking](./SEARCH_ARCHITECTURE_03_RELEVANCE.md)

---

## Table of Contents

1. [Search Interface Design](#search-interface-design)
2. [Autocomplete & Suggestions](#autocomplete-suggestions)
3. [Faceted Search](#faceted-search)
4. [Results Display](#results-display)
5. [Empty States](#empty-states)
6. [Search Behavior Tracking](#search-behavior-tracking)

---

## Search Interface Design

### Search Component Structure

```typescript
// Search component architecture

interface SearchComponents {
  // Search input
  searchInput: {
    component: 'SearchInput';
    features: [
      'Debounced input',
      'Clear button',
      'Loading indicator',
      'Query highlighting',
      'Recent searches',
    ];
  };

  // Autocomplete dropdown
  autocomplete: {
    component: 'SearchAutocomplete';
    sections: [
      'Quick suggestions',
      'Destinations',
      'Accommodations',
      'Deals',
    ];
  };

  // Results page
  resultsPage: {
    components: [
      'SearchBar (persistent)',
      'FacetFilters',
      'ActiveFilters',
      'ResultsList',
      'Pagination',
      'SortOptions',
    ];
  };
}
```

### Search Input Component

```typescript
// React search input with debouncing

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { useRouter, useSearchParams } from 'next/navigation';

export function SearchInput() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search
  const debouncedSearch = useDebouncedCallback(
    (value: string) => {
      if (value.trim()) {
        router.push(`/search?q=${encodeURIComponent(value)}`);
      } else {
        router.push('/search');
      }
    },
    300 // 300ms delay
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
    setIsOpen(true);
  };

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
    router.push('/search');
  };

  return (
    <div className="search-container">
      <div className="search-input-wrapper">
        <SearchIcon className="search-icon" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          onFocus={() => setIsOpen(true)}
          placeholder="Search destinations, hotels, deals..."
          className="search-input"
          autoComplete="off"
        />
        {query && (
          <button onClick={handleClear} className="clear-button">
            <CloseIcon />
          </button>
        )}
      </div>

      {isOpen && query && (
        <SearchAutocomplete
          query={query}
          onClose={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
```

---

## Autocomplete Suggestions

### Query Suggestions

```typescript
// Algolia Query Suggestions

import { searchClient } from '@/lib/algolia';

export async function getQuerySuggestions(query: string) {
  const suggestionsIndex = searchClient.initIndex(
    'travel_query_suggestions'
  );

  const results = await suggestionsIndex.search(query, {
    hitsPerPage: 5,
  });

  return results.hits.map((hit) => hit.query);
}

// Create query suggestions index from popular searches
async function buildQuerySuggestions() {
  const analytics = await getPopularSearchQueries({
    minHits: 10,
    days: 30,
  });

  const suggestions = analytics.map((query) => ({
    objectID: query.query,
    query: query.query,
    popularity: query.count,
  }));

  const index = algoliaAdmin.initIndex('travel_query_suggestions');
  await index.saveObjects(suggestions);
}
```

### Instant Search Results

```typescript
// Real-time autocomplete with results

'use client';

import { useInstantSearch } from 'react-instantsearch';
import { Highlight, Snippet } from 'react-instantsearch';

export function SearchAutocomplete({ query }: { query: string }) {
  const { indices } = useInstantSearch();

  return (
    <div className="autocomplete-dropdown">
      {/* Query suggestions */}
      <QuerySuggestions query={query} />

      {/* Destinations */}
      <AutocompleteSection
        title="Destinations"
        indexName="travel_destinations"
        hitComponent={DestinationHit}
      />

      {/* Accommodations */}
      <AutocompleteSection
        title="Accommodations"
        indexName="travel_accommodations"
        hitComponent={AccommodationHit}
      />

      {/* Deals */}
      <AutocompleteSection
        title="Deals"
        indexName="travel_deals"
        hitComponent={DealHit}
      />
    </div>
  );
}

function DestinationHit({ hit }: { hit: DestinationHit }) {
  return (
    <Link
      href={`/destinations/${hit.slug}`}
      className="autocomplete-hit"
    >
      <img src={hit.imageUrl} alt="" className="hit-image" />
      <div className="hit-content">
        <Highlight hit={hit} attribute="title" />
        <span className="hit-location">{hit.country}</span>
      </div>
    </Link>
  );
}
```

### Recent Searches

```typescript
// Local storage-based recent searches

const RECENT_SEARCHES_KEY = 'recent_searches';
const MAX_RECENT = 5;

export function useRecentSearches() {
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (stored) {
      setRecent(JSON.parse(stored));
    }
  }, []);

  const addRecent = useCallback((query: string) => {
    if (!query.trim()) return;

    setRecent((prev) => {
      const filtered = prev.filter((q) => q !== query);
      const updated = [query, ...filtered].slice(0, MAX_RECENT);
      localStorage.setItem(
        RECENT_SEARCHES_KEY,
        JSON.stringify(updated)
      );
      return updated;
    });
  }, []);

  const clearRecent = useCallback(() => {
    setRecent([]);
    localStorage.removeItem(RECENT_SEARCHES_KEY);
  }, []);

  return { recent, addRecent, clearRecent };
}

// Display in autocomplete
function RecentSearches({
  searches,
  onSelect,
}: {
  searches: string[];
  onSelect: (query: string) => void;
}) {
  if (searches.length === 0) return null;

  return (
    <div className="recent-searches">
      <div className="recent-header">
        <span>Recent Searches</span>
        <button onClick={() => clearRecent()}>Clear</button>
      </div>
      <ul className="recent-list">
        {searches.map((query) => (
          <li key={query}>
            <button onClick={() => onSelect(query)}>
              <ClockIcon />
              {query}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Faceted Search

### Filter Configuration

```typescript
// Facet configuration by content type

interface FacetConfig {
  destinations: [
    {
      attribute: 'country';
      type: 'filter';
      label: 'Country';
      sort: 'count:desc';
    },
    {
      attribute: 'region';
      type: 'filter';
      label: 'Region';
      sort: 'alpha:asc';
    },
    {
      attribute: 'bestTimeToVisit';
      type: 'filter';
      label: 'Best Time to Visit';
      sort: 'alpha:asc';
    },
  ];

  accommodations: [
    {
      attribute: 'type';
      type: 'filter';
      label: 'Property Type';
      options: ['Hotel', 'Resort', 'Villa', 'Apartment'];
    },
    {
      attribute: 'starRating';
      type: 'menu';
      label: 'Star Rating';
      sort: 'desc';
    },
    {
      attribute: 'amenities';
      type: 'refinementList';
      label: 'Amenities';
      limit: 10;
    },
    {
      attribute: 'pricePerNight';
      type: 'range';
      label: 'Price per Night';
      min: 0;
      max: 1000;
    },
    {
      attribute: 'rating';
      type: 'range';
      label: 'Guest Rating';
      min: 0;
      max: 5;
    },
  ];
}
```

### Facet Component

```typescript
// Refinement list component

'use client';

import { useRefinementList, useRange } from 'react-instantsearch';

export function FilterPanel() {
  return (
    <aside className="filter-panel">
      <ActiveFilters />
      <RefinementList
        attribute="country"
        label="Country"
        limit={10}
        showMore
      />
      <RefinementList
        attribute="type"
        label="Property Type"
        limit={5}
      />
      <StarRatingFilter />
      <PriceRangeFilter />
      <AmenityFilter />
      <ClearFilters />
    </aside>
  );
}

function RefinementList({
  attribute,
  label,
  limit,
  showMore,
}: {
  attribute: string;
  label: string;
  limit?: number;
  showMore?: boolean;
}) {
  const {
    items,
    refine,
    canToggleShowMore,
    isShowingMore,
    toggleShowMore,
  } = useRefinementList({
    attribute,
    limit,
    showMore: true,
  });

  return (
    <div className="filter-group">
      <h3>{label}</h3>
      <ul>
        {items.map((item) => (
          <li key={item.label}>
            <label>
              <input
                type="checkbox"
                checked={item.isRefined}
                onChange={() => refine(item.value)}
              />
              <span>{item.label}</span>
              <span className="count">({item.count})</span>
            </label>
          </li>
        ))}
      </ul>
      {showMore && canToggleShowMore && (
        <button onClick={toggleShowMore}>
          {isShowingMore ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}
```

### Range Slider Filter

```typescript
// Numeric range filter

'use client';

import { useRange } from 'react-instantsearch';
import 'rheostat/initialize';

export function PriceRangeFilter() {
  const { start, range, canRefine, refine } = useRange({
    attribute: 'pricePerNight',
    min: 0,
    max: 1000,
  });

  if (!canRefine) return null;

  return (
    <div className="filter-group">
      <h3>Price per Night</h3>
      <Rheostat
        min={range?.min || 0}
        max={range?.max || 1000}
        values={[start[0], start[1]]}
        onChange={({ values }) => refine(values)}
      />
      <div className="range-labels">
        <span>${start[0]}</span>
        <span>${start[1]}</span>
      </div>
    </div>
  );
}
```

### Active Filters Display

```typescript
// Show and clear active filters

'use client';

import { useCurrentRefinements, useClearRefinements } from 'react-instantsearch';

export function ActiveFilters() {
  const { items, canRefine } = useCurrentRefinements();
  const { refine } = useClearRefinements();

  if (!canRefine) return null;

  return (
    <div className="active-filters">
      <span className="filter-label">Active filters:</span>
      {items.map((item) => (
        <span key={item.index} className="active-filter">
          {item.label}: {item.currentRefinement}
          <button
            onClick={() => item.refine(item.currentRefinement)}
            aria-label="Remove filter"
          >
            ×
          </button>
        </span>
      ))}
      <button onClick={() => refine()} className="clear-all">
        Clear all
      </button>
    </div>
  );
}
```

---

## Results Display

### Results List Component

```typescript
// Search results list

'use client';

import { useHits, usePagination } from 'react-instantsearch';

export function SearchResults() {
  const { hits, results } = useHits();
  const { currentRefinement, nbPages, refine } = usePagination();

  return (
    <div className="search-results">
      <ResultsHeader results={results} />

      <div className="results-list">
        {hits.map((hit) => (
          <SearchResultCard key={hit.objectID} hit={hit} />
        ))}
      </div>

      {nbPages > 1 && (
        <Pagination
          currentPage={currentRefinement + 1}
          totalPages={nbPages}
          onPageChange={(page) => refine(page - 1)}
        />
      )}
    </div>
  );
}

function ResultsHeader({ results }: { results: SearchResults }) {
  return (
    <div className="results-header">
      <p>
        {results.nbHits} results for "<strong>{results.query}</strong>"
        {results.processingTimeMS && (
          <span className="time"> in {(results.processingTimeMS / 1000).toFixed(2)}s</span>
        )}
      </p>

      <SortSelector />
    </div>
  );
}
```

### Result Card Component

```typescript
// Individual search result card

function SearchResultCard({ hit }: { hit: Hit }) {
  return (
    <article className="result-card">
      <Link href={hit.url} className="result-link">
        {/* Image */}
        <div className="result-image">
          <img src={hit.imageUrl} alt={hit.title} loading="lazy" />
          {hit.featured && <span className="featured-badge">Featured</span>}
          {hit.discount && (
            <span className="discount-badge">-{hit.discount}%</span>
          )}
        </div>

        {/* Content */}
        <div className="result-content">
          {/* Title with highlighting */}
          <h3>
            <Highlight hit={hit} attribute="title" />
          </h3>

          {/* Snippet */}
          <p className="result-description">
            <Snippet hit={hit} attribute="description" />
          </p>

          {/* Metadata */}
          <div className="result-meta">
            {hit.rating && (
              <span className="rating">
                <StarIcon />
                {hit.rating}
              </span>
            )}
            {hit.location && (
              <span className="location">
                <LocationIcon />
                {hit.location}
              </span>
            )}
            {hit.price && (
              <span className="price">
                From ${hit.price}
              </span>
            )}
          </div>
        </div>
      </Link>
    </article>
  );
}
```

### Sort Options

```typescript
// Sort selector component

'use client';

import { connectSortBy } from 'react-instantsearch';

const SortBy = connectSortBy(({ items, currentRefinement, refine }) => (
  <div className="sort-selector">
    <label htmlFor="sort">Sort by:</label>
    <select
      id="sort"
      value={currentRefinement}
      onChange={(e) => refine(e.target.value)}
    >
      {items.map((item) => (
        <option key={item.value} value={item.value}>
          {item.label}
        </option>
      ))}
    </select>
  </div>
));

export function SortSelector() {
  return (
    <SortBy
      items={[
        { label: 'Relevance', value: 'travel_destinations' },
        { label: 'Most Popular', value: 'travel_destinations_by_popularity' },
        { label: 'Highest Rated', value: 'travel_destinations_by_rating' },
        { label: 'Newest', value: 'travel_destinations_by_newest' },
      ]}
    />
  );
}
```

---

## Empty States

### No Results State

```typescript
// Helpful no results message

'use client';

import { useSearchBox } from 'react-instantsearch';

export function NoResults() {
  const { query } = useSearchBox();

  return (
    <div className="no-results">
      <div className="no-results-icon">
        <SearchIcon />
      </div>
      <h2>No results for "{query}"</h2>
      <p>Try adjusting your search or filters to find what you're looking for.</p>

      <Suggestions query={query} />

      <div className="no-results-actions">
        <button onClick={clearFilters}>Clear all filters</button>
        <button onClick={startOver}>Start a new search</button>
      </div>
    </div>
  );
}

function Suggestions({ query }: { query: string }) {
  // Get query suggestions
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    getQuerySuggestions(query).then(setSuggestions);
  }, [query]);

  if (suggestions.length === 0) return null;

  return (
    <div className="suggestions">
      <p>Did you mean:</p>
      <ul>
        {suggestions.map((suggestion) => (
          <li key={suggestion}>
            <Link href={`/search?q=${encodeURIComponent(suggestion)}`}>
              {suggestion}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Empty Search State

```typescript
// Initial search page state

export function EmptySearchState() {
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('recent_searches');
    if (stored) setRecent(JSON.parse(stored));
  }, []);

  return (
    <div className="empty-search">
      <h1>Where do you want to go?</h1>
      <SearchInput />

      {recent.length > 0 && (
        <div className="recent-searches">
          <h3>Recent Searches</h3>
          <ul>
            {recent.map((query) => (
              <li key={query}>
                <Link href={`/search?q=${encodeURIComponent(query)}`}>
                  {query}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <PopularDestinations />
      <TrendingDeals />
    </div>
  );
}
```

---

## Search Behavior Tracking

### Event Tracking

```typescript
// Track search interactions

'use client';

import { useInstantSearch, useSearchBox, useHits } from 'react-instantsearch';

export function SearchAnalytics() {
  const { indexUiState } = useInstantSearch();
  const { query } = useSearchBox();
  const { hits } = useHits();

  useEffect(() => {
    if (query) {
      // Track search query
      trackSearch({
        query,
        index: indexUiState.indexName || 'destinations',
        filters: indexUiState.refinementList,
        resultsCount: hits.length,
      });
    }
  }, [query, indexUiState, hits.length]);

  return null;
}

// Track result clicks
export function TrackClick({ hit, position }: { hit: Hit; position: number }) {
  const handleClick = () => {
    trackClick({
      queryId: hit.__queryID,
      position,
      objectId: hit.objectID,
      index: hit.__indexName,
    });
  };

  return <a onClick={handleClick}>{hit.title}</a>;
}

// Track conversions
export function trackConversion(objectId: string, queryId: string) {
  analytics.track('search_conversion', {
    queryId,
    objectId,
    value: getBookingValue(),
  });
}
```

---

## Summary

Search UX for the travel agency platform:

- **Interface**: Debounced input, clear button, recent searches
- **Autocomplete**: Query suggestions, instant results, categories
- **Faceted Search**: Filters, ranges, active filters display
- **Results**: Highlighted matches, snippets, sort options
- **Empty States**: Helpful messages, suggestions, popular content
- **Tracking**: Query, click, and conversion analytics

**Key UX Decisions:**
- 300ms debounce for search input
- Multi-section autocomplete
- Faceted filters with counts
- Highlighted query matches in results
- Sort options (relevance, popularity, rating, newest)
- Helpful empty states with suggestions

---

**Series Complete:** [Search Architecture Master Index](./SEARCH_ARCHITECTURE_MASTER_INDEX.md)
