# Data Architecture

**Date**: 2026-04-15  
**Status**: Documented  

---

## Overview

The Travel Agency Agent requires geographic city data for destination recognition. The data layer follows a tiered approach with static datasets, runtime accumulation, and clear separation between code and data assets.

---

## Data Sources

### 1. Base Datasets (Downloaded)

| File | Size | Source | Purpose |
|------|------|--------|---------|
| `data/cities5000.txt` | ~145MB | GeoNames (CC-BY 4.0) | Cities with population > 5000 |
| `data/cities.json` | ~41MB | world-cities.json (ODbL-1.0) | Supplemental dataset |

**Exclusion from Git**: These files are excluded from version control due to size. They are downloaded during deployment or setup.

### 2. Runtime Data (Generated)

| File | Size | Purpose |
|------|------|---------|
| `data/accumulated_cities.json` | Small (<1MB) | Cities learned from user messages |
| `data/accumulated_cities.lock` | Tiny | Lock file for concurrent access |

**Exclusion from Git**: Generated at runtime. Each deployment starts fresh or loads from external state store.

---

## Production Deployment Strategy

### Option A: Download at Build Time (Recommended)

Modify Dockerfile to fetch datasets during image build:

```dockerfile
# In Dockerfile, after COPY data/ and before runtime
RUN curl -L -o data/cities5000.txt https://download.geonames.org/export/dump/cities5000.zip \
    && unzip data/cities5000.zip -d data/ \
    && rm data/cities5000.zip

RUN curl -L -o data/cities.json https://raw.githubusercontent.com/lutangar/cities.json/master/cities.json
```

**Pros**: No runtime downloads, self-contained image  
**Cons**: Build time increases by ~2-3 minutes  

### Option B: Fly.io Volumes (Persistent Storage)

For Fly.io deployments:

1. Create volume: `fly volumes create data --size 1`
2. Mount in fly.toml: `[[mounts]] destination = "/app/data"`
3. Run download script on first boot

**Pros**: Faster builds, data persists across deploys  
**Cons**: Requires volume management, complicates horizontal scaling  

### Option C: S3/R2 External Storage

Store datasets in cloud object storage, download at container startup:

```python
# startup.py
if not CITY_DATA.exists():
    download_from_s3("s3://bucket/cities5000.txt", CITY_DATA)
```

**Pros**: Datasets can be updated without rebuild  
**Cons**: Cold start latency, requires credentials management  

---

## Current Implementation

### Code Structure

```
data/
├── README.md              # Data documentation
├── cities5000.txt       # GeoNames (gitignored)
├── cities.json          # world-cities.json (gitignored)
├── accumulated_cities.json  # Runtime data (gitignored)
├── accumulated_cities.lock  # Lock file (gitignored)
└── fixtures/            # Test scenarios (version controlled)
```

### Usage in Code

```python
# src/intake/geography.py
_DATA_PATH = Path(__file__).parent.parent / "data"
_GEONAMES_PATH = _DATA_PATH / "cities5000.txt"
_WORLDCITIES_PATH = _DATA_PATH / "cities.json"
_ACCUMULATED_PATH = _DATA_PATH / "accumulated_cities.json"

def load_city_database():
    # Loads from all three sources
    cities = load_geonames()  # From cities5000.txt
    cities.update(load_worldcities())  # From cities.json
    cities.update(load_accumulated())  # From accumulated_cities.json
    return cities
```

---

## Development Setup

For local development, download datasets once:

```bash
# Run setup script (to be implemented)
./scripts/setup-data.sh

# Or manually
cd data
curl -L -o cities5000.txt https://download.geonames.org/export/dump/cities5000.zip
unzip cities5000.zip
rm cities5000.zip

curl -L -o cities.json https://raw.githubusercontent.com/lutangar/cities.json/master/cities.json
```

---

## Migration Path

To implement "download at build time" (Option A):

1. Create `scripts/setup-data.sh` - Download script
2. Update Dockerfile - Call download script
3. Update `.dockerignore` - Keep data/ files
4. Test build locally
5. Update CI/CD to include data download

---

## Open Questions

- Which option should be default for production?
- Should we cache datasets in CI/CD?
- Do we need geographic data versioning?

---

## Related Files

- `.gitignore` - Data file exclusions
- `Dockerfile` - Build configuration
- `src/intake/geography.py` - Data consumer
- `tests/test_geography.py` - Data tests
