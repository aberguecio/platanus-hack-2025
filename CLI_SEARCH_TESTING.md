# CLI Search Testing Guide

This guide explains how to test the semantic search and embeddings functionality using the CLI tools.

## Overview

Two testing tools are available:

1. **Python CLI** (`backend/cli_search.py`) - Full-featured testing script
2. **Bash Wrapper** (`scripts/test_search.sh`) - Easy-to-use wrapper

Both provide the same functionality but the bash wrapper is more convenient for quick testing.

---

## Quick Start

### Prerequisites

Containers must be running:

```bash
docker compose -f docker-compose.local.yml up -d
```

### Basic Usage

```bash
# Using bash wrapper (recommended)
./scripts/test_search.sh search "beach photos"

# Or using Python directly
docker compose -f docker-compose.local.yml exec backend python cli_search.py search "beach photos"
```

---

## Commands

### 1. Search Memories

Search across all memories or within a specific event.

**Syntax:**
```bash
./scripts/test_search.sh search "<query>" [options]
```

**Options:**
- `--event-id <id>` - Limit search to specific event
- `--top-k <n>` - Number of results (default: 10)
- `--threshold <0-1>` - Minimum similarity score (default: 0.0)

**Examples:**

```bash
# Search all memories
./scripts/test_search.sh search "beach sunset"

# Search within specific event
./scripts/test_search.sh search "team photo" --event-id 1

# Get top 20 results
./scripts/test_search.sh search "celebration" --top-k 20

# Only show high-quality matches (80%+)
./scripts/test_search.sh search "birthday cake" --threshold 0.8
```

**Sample Output:**

```
🔍 Searching for: 'beach sunset'
   Top 10 results

✅ Found 3 results:

================================================================================

1. 🎯 EXCELLENT (92.5% match)
   Memory ID: #42
   Event: Summer Vacation
   Text: Beautiful sunset at the beach with friends
   Has image: Yes
   Created: 2025-11-20 18:30

2. ✨ GOOD (78.3% match)
   Memory ID: #55
   Event: Weekend Trip
   Text: Evening walk by the ocean
   Has image: No
   Created: 2025-11-21 19:15

3. 📌 MODERATE (65.1% match)
   Memory ID: #61
   Event: Road Trip
   Text: Stopped at coastal viewpoint
   Has image: Yes
   Created: 2025-11-19 17:45

================================================================================
```

**Similarity Indicators:**
- 🎯 EXCELLENT (80%+) - Very high relevance
- ✨ GOOD (60-79%) - Good match
- 📌 MODERATE (40-59%) - Moderate relevance
- 📍 LOW (<40%) - Low relevance

---

### 2. Show Statistics

Display embedding coverage and database statistics.

**Syntax:**
```bash
./scripts/test_search.sh stats
```

**Example:**

```bash
./scripts/test_search.sh stats
```

**Sample Output:**

```
📊 Embedding Statistics

============================================================
Total memories:           150
Searchable (with embed):  120
Unsearchable (no embed):  30
Coverage:                 80.0%

============================================================

Total events:             8
Total users:              5
Events with searchable memories: 7/8
```

**Use Cases:**
- Check if embeddings are being generated
- Monitor coverage after adding memories
- Identify memories without embeddings

---

### 3. Find Similar Memories

Find memories semantically similar to a specific memory.

**Syntax:**
```bash
./scripts/test_search.sh similar <memory_id> [options]
```

**Options:**
- `--top-k <n>` - Number of results (default: 5)
- `--threshold <0-1>` - Minimum similarity (default: 0.5)

**Examples:**

```bash
# Find memories similar to memory #42
./scripts/test_search.sh similar 42

# Get top 10 similar memories
./scripts/test_search.sh similar 42 --top-k 10

# Only show very similar (70%+)
./scripts/test_search.sh similar 42 --threshold 0.7
```

**Sample Output:**

```
🔗 Finding memories similar to:

Memory #42:
  Event: #1
  User: #5
  Text: Beautiful sunset at the beach with friends
  Image: Yes
  Embedding: Yes
  Created: 2025-11-20T18:30:00

================================================================================

✅ Found 3 similar memories:

1. Similarity: 85.3%
   Memory ID: #55
   Event: Weekend Trip
   Text: Evening beach walk with spectacular colors in the sky

2. Similarity: 78.9%
   Memory ID: #61
   Event: Road Trip
   Text: Stopped at coastal viewpoint, amazing sunset

3. Similarity: 72.1%
   Memory ID: #73
   Event: Summer Vacation
   Text: Last evening at the beach house
```

**Use Cases:**
- Discover related memories
- Group similar content
- Test embedding quality

---

### 4. List Memories

List memories with optional filters.

**Syntax:**
```bash
./scripts/test_search.sh list [options]
```

**Options:**
- `--event-id <id>` - Filter by event
- `--with-embeddings` - Only show memories with embeddings
- `--without-embeddings` - Only show memories without embeddings
- `--limit <n>` - Max results (default: 20)
- `--show-embedding-info` - Show embedding details (dims, sample values)

**Examples:**

```bash
# List all memories (first 20)
./scripts/test_search.sh list

# List memories with embeddings
./scripts/test_search.sh list --with-embeddings

# List memories without embeddings (need fixing)
./scripts/test_search.sh list --without-embeddings

# List memories in specific event
./scripts/test_search.sh list --event-id 1

# Get more results
./scripts/test_search.sh list --limit 50

# Show embedding details
./scripts/test_search.sh list --with-embeddings --show-embedding-info
```

**Sample Output:**

```
📋 All memories:

   (showing only memories with embeddings)

✅ Found 20 memories:

================================================================================

Memory #42:
  Event: #1
  User: #5
  Text: Beautiful sunset at the beach with friends
  Image: Yes
  Embedding: Yes
  Created: 2025-11-20T18:30:00
  Embedding dims: 1024
  First 5 values: [0.123, -0.456, 0.789, -0.234, 0.567]
--------------------------------------------------------------------------------

Memory #41:
  Event: #1
  User: #5
  Text: Lunch at the beachside restaurant
  Image: Yes
  Embedding: Yes
  Created: 2025-11-20T13:15:00
--------------------------------------------------------------------------------
```

**Use Cases:**
- Audit embedding coverage
- Find memories that need re-processing
- Debug embedding generation issues

---

### 5. Test Multiple Queries

Test many queries at once from a file.

**Syntax:**
```bash
./scripts/test_search.sh test-queries <file>
```

**Example:**

```bash
# Test with sample queries
./scripts/test_search.sh test-queries scripts/sample_queries.txt

# Create custom query file
cat > my_queries.txt << EOF
beach photos
team dinner
sunset views
birthday party
EOF

./scripts/test_search.sh test-queries my_queries.txt
```

**Query File Format:**

```text
# Comments start with #
# One query per line

beach sunset
team dinner photos
celebration moments
outdoor activities
```

**Sample Output:**

```
🧪 Testing 4 queries

================================================================================

[1/4] Query: 'beach sunset'
   Results: 5
   Avg similarity: 75.3%
   Top match: 92.5%

[2/4] Query: 'team dinner'
   Results: 8
   Avg similarity: 82.1%
   Top match: 95.2%

[3/4] Query: 'celebration moments'
   Results: 12
   Avg similarity: 78.9%
   Top match: 89.7%

[4/4] Query: 'outdoor activities'
   Results: 15
   Avg similarity: 71.4%
   Top match: 85.3%

================================================================================

📈 Summary:

Successful queries: 4/4
Failed queries: 0/4

Average results per query: 10.0
Average similarity score: 76.9%

Best query: 'team dinner' (95.2%)
Worst query: 'outdoor activities' (85.3%)
```

**Use Cases:**
- Benchmark search quality
- Test query variations
- Regression testing after changes
- Performance evaluation

---

## Usage Patterns

### Development Workflow

```bash
# 1. Check current status
./scripts/test_search.sh stats

# 2. List memories without embeddings (if coverage < 100%)
./scripts/test_search.sh list --without-embeddings

# 3. After fixing embeddings, verify
./scripts/test_search.sh stats

# 4. Test search quality
./scripts/test_search.sh search "test query"

# 5. Run comprehensive tests
./scripts/test_search.sh test-queries scripts/sample_queries.txt
```

### Debugging Failed Searches

```bash
# 1. Check if any memories have embeddings
./scripts/test_search.sh stats

# 2. List searchable memories
./scripts/test_search.sh list --with-embeddings --limit 5

# 3. Check embedding dimensions
./scripts/test_search.sh list --with-embeddings --show-embedding-info --limit 1

# 4. Try broad query
./scripts/test_search.sh search "photo" --top-k 20

# 5. Lower threshold if no results
./scripts/test_search.sh search "your query" --threshold 0.0
```

### Quality Assurance

```bash
# Create test suite
cat > qa_queries.txt << EOF
# Core functionality tests
test memory
sample text
example photo

# Edge cases
very specific unique query
common generic word
multi word phrase with details
EOF

# Run tests
./scripts/test_search.sh test-queries qa_queries.txt

# Analyze results
# - Should find something for common terms
# - May return nothing for very specific queries
# - Multi-word phrases should work well
```

---

## Advanced Usage

### Using Python CLI Directly

For more control or scripting:

```bash
# Inside container
docker compose exec backend bash
python cli_search.py search "query" --top-k 10

# From host with docker exec
docker compose exec backend python cli_search.py stats

# With -T flag for scripting (no TTY)
docker compose exec -T backend python cli_search.py search "query"
```

### Scripting

```bash
#!/bin/bash
# Automated search quality report

echo "=== Search Quality Report ===" > report.txt
echo "" >> report.txt

# Statistics
echo "## Statistics" >> report.txt
./scripts/test_search.sh stats >> report.txt
echo "" >> report.txt

# Test queries
echo "## Test Results" >> report.txt
./scripts/test_search.sh test-queries scripts/sample_queries.txt >> report.txt

echo "Report saved to report.txt"
```

### Programmatic Usage

```python
# Direct Python usage (inside container)
from database import SessionLocal
from services.search import SearchService

db = SessionLocal()

results = SearchService.search_memories(
    db=db,
    query="beach photos",
    top_k=10,
    threshold=0.0
)

for result in results:
    print(f"{result.id}: {result.similarity_score:.2%}")

db.close()
```

---

## Troubleshooting

### No Results Found

**Check:**
1. Do any memories have embeddings?
   ```bash
   ./scripts/test_search.sh stats
   ```

2. List searchable memories:
   ```bash
   ./scripts/test_search.sh list --with-embeddings
   ```

3. Try very broad query:
   ```bash
   ./scripts/test_search.sh search "the" --top-k 20
   ```

**Common causes:**
- No memories with embeddings yet
- VOYAGE_API_KEY not set
- Embedding generation failed

### "Backend container is not running"

```bash
# Start containers
docker compose -f docker-compose.local.yml up -d

# Check status
docker compose -f docker-compose.local.yml ps
```

### "Failed to generate embedding"

**Check environment:**
```bash
docker compose exec backend env | grep VOYAGE_API_KEY
```

**Test Voyage AI directly:**
```bash
docker compose exec backend python
>>> from services.embedding import EmbeddingService
>>> emb = EmbeddingService.embed_text("test", input_type="query")
>>> len(emb)
1024
```

### Low Similarity Scores

This is normal! Semantic search doesn't require exact matches:

- **90%+** = Excellent (almost identical)
- **70-90%** = Very good (clearly related)
- **50-70%** = Good (semantically similar)
- **30-50%** = Fair (loosely related)
- **<30%** = Poor (not very relevant)

Lower your threshold if needed:
```bash
./scripts/test_search.sh search "query" --threshold 0.3
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Test Search Functionality
  run: |
    docker compose -f docker-compose.local.yml up -d
    sleep 10  # Wait for services

    # Run tests
    docker compose -f docker-compose.local.yml exec -T backend \
      python cli_search.py stats

    docker compose -f docker-compose.local.yml exec -T backend \
      python cli_search.py test-queries scripts/sample_queries.txt
```

---

## Performance Notes

- **Search speed**: ~100-500ms for 1,000 memories (with HNSW index)
- **Embedding generation**: ~200-500ms per text
- **Batch operations**: Use test-queries for efficiency
- **Database**: PostgreSQL with pgvector handles 10k+ memories easily

---

## Next Steps

1. **Add memories** with the Telegram bot
2. **Verify embeddings** are generated:
   ```bash
   ./scripts/test_search.sh stats
   ```

3. **Test search** with your content:
   ```bash
   ./scripts/test_search.sh search "your query"
   ```

4. **Create test suite** for your use case:
   ```bash
   cat > my_tests.txt << EOF
   # Your specific queries
   EOF

   ./scripts/test_search.sh test-queries my_tests.txt
   ```

5. **Monitor quality** as you add more memories

---

## Summary

| Command | Purpose | Quick Example |
|---------|---------|---------------|
| `search` | Find memories by query | `./scripts/test_search.sh search "beach"` |
| `stats` | Check embedding coverage | `./scripts/test_search.sh stats` |
| `similar` | Find related memories | `./scripts/test_search.sh similar 42` |
| `list` | View all memories | `./scripts/test_search.sh list --with-embeddings` |
| `test-queries` | Batch testing | `./scripts/test_search.sh test-queries file.txt` |

**For help:**
```bash
./scripts/test_search.sh --help
```

Happy testing! 🔍✨
