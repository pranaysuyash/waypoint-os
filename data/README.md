# Data Directory

This directory contains datasets used by the intake engine for geography recognition.

## Files

### cities5000.txt

**Source**: [GeoNames](https://download.geonames.org/export/dump/) (cities5000.zip)
**License**: CC-BY 4.0 (attribution required)
**Size**: ~14MB
**Cities**: ~68,000 cities with population > 5,000

**Format**: Tab-separated values

```
geonameid	name	asciiname	alternatenames	feature	class	featurecode	countrycode	...	population	...
```

**Usage**: Primary city database for origin/destination extraction.

**Attribution**: Any UI using this data must include:

```html
Location data © <a href="https://www.geonames.org/">GeoNames</a>
```

---

### cities.json

**Source**: [countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database)
**Path**: `json/countries+cities.json`
**License**: ODbL-1.0 (Open Database License) — share-alike obligations apply
**Size**: ~4MB
**Cities**: ~135,000 cities

**Format**: JSON array of country objects with nested cities arrays

```json
[
  {
    "name": "Afghanistan",
    "cities": ["City1", "City2", ...]
  },
  ...
]
```

**Usage**: Supplemental city database, fills gaps in GeoNames coverage.

**⚠️ License Note**: This dataset is ODbL-1.0, which has share-alike obligations.
Any derivative database or product using this data must also be shared under ODbL-1.0.
This conflicts with a proprietary/closed-source model. If proprietary licensing is required,
consider replacing this dataset with an MIT/CC0-licensed alternative.

---

### accumulated_cities.json

**Purpose**: Organic accumulation of cities seen in real user messages
**License**: Project license
**Format**: JSON array of city names (strings)
**Initial state**: Empty array `[]`

**How cities are added**:

- Confidence score > 0.7 (reasonably sure it's a city)
- Not already in baseline datasets
- Not a blacklisted term (common travel words)
- Added via `record_seen_city()` in `src/intake/geography.py`

**Note**: This file is in `.gitignore` - it's generated locally and shouldn't be committed.

---

## Statistics

As of initial setup:

| Source                          | Cities   |
| ------------------------------- | -------- |
| GeoNames (with alternate names) | ~504,000 |
| world-cities.json               | ~135,000 |
| Total unique                    | ~589,000 |

---

## Refreshing Data

### GeoNames

GeoNames is updated daily. To refresh:

```bash
cd data/
curl -O https://download.geonames.org/export/dump/cities5000.zip
unzip -o cities5000.zip
rm cities5000.zip
```

### world-cities.json

Check the [GitHub repo](https://github.com/dr5hn/countries-states-cities-database) for updates.

---

## Implementation

The geography database is implemented in `src/intake/geography.py`:

- `is_known_city(name)` - Check if a name is a known city
- `is_known_city_normalized(name)` - Case-insensitive lookup
- `record_seen_city(city, confidence)` - Add new city organically
- `get_dataset_info()` - Get statistics about loaded data
- `get_attribution_notice()` - Get GeoNames attribution string
