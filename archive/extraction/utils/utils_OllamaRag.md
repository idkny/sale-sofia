---
id: extraction_ollamarag_utils
type: extraction
subject: utils
source_repo: Ollama-Rag
description: "Utility functions from Ollama-Rag - URL handling, file operations"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, utils, file-handling, url, ollamarag]
---

# Utility Functions - Ollama-Rag

**Source**: `utils.py`
**Purpose**: URL file processing, data file handling
**Status**: SPECIALIZED for GitHub URL processing

---

## 1. URL File Deduplication and Cleaning

```python
# Source: utils.py:396-416
def clean_file_new_urls(file_path):
    """
    Reads URLs from file, deduplicates, and filters to GitHub URLs only.
    Extracts owner/repo path from full URLs.

    Args:
        file_path: Path to file containing URLs

    Returns:
        list: Clean GitHub paths (owner/repo format)
    """
    with open(file_path, 'r') as file:
        page_urls = [line.strip() for line in file.readlines()]

    # Deduplicate
    page_urls = list(set(page_urls))

    github_prefix = "https://github.com/"
    clean_urls = []
    valid_urls = []

    for url in page_urls:
        if url.startswith(github_prefix):
            clean_urls.append(url[len(github_prefix):])  # Extract owner/repo
            valid_urls.append(url)

    valid_urls.sort()

    # Rewrite file with cleaned, sorted URLs
    with open(file_path, 'w') as file:
        for url in valid_urls:
            file.write(url + '\n')

    return clean_urls
```

### Key Features

- **Deduplication** - `list(set(urls))`
- **URL validation** - Only keeps GitHub URLs
- **Path extraction** - `https://github.com/owner/repo` → `owner/repo`
- **In-place cleanup** - Rewrites source file
- **Sorted output** - Alphabetical order

---

## 2. URL File Merge Pattern

```python
# Source: utils.py:334-366
def append_to_existing_urls_in_db_file():
    """
    Reads URLs from 'urls_list.txt', appends them to 'existing_urls_in_db.txt',
    and then deletes the contents of 'urls_list.txt'.
    Both files are located in the 'data' folder under the project root.

    Pattern: Process new items → Append to processed list → Clear inbox
    """
    try:
        # Define file paths
        project_root = os.getcwd()
        data_folder = os.path.join(project_root, "data")
        urls_list_file = os.path.join(data_folder, "urls_list.txt")
        existing_urls_file = os.path.join(data_folder, "existing_urls_in_db.txt")

        # Check if the input file exists
        if not os.path.exists(urls_list_file):
            raise FileNotFoundError(f"Input file not found: {urls_list_file}")

        # Read URLs from 'urls_list.txt'
        with open(urls_list_file, "r") as infile:
            urls = infile.readlines()

        # Append URLs to 'existing_urls_in_db.txt'
        with open(existing_urls_file, "a") as outfile:
            for url in urls:
                outfile.write(url.strip() + "\n")

        # Clear the contents of 'urls_list.txt'
        with open(urls_list_file, "w") as infile:
            infile.write("")  # Overwrite with an empty file

        print(f"Successfully appended URLs to {existing_urls_file} and cleared {urls_list_file}.")
    except Exception as e:
        print(f"An error occurred: {e}")
```

### Inbox Pattern

```
urls_list.txt (inbox - new items)
       ↓
  Process items
       ↓
existing_urls_in_db.txt (processed log)
       ↓
  Clear inbox
```

---

## 3. Check for New URLs

```python
# Source: utils.py:368-394
def check_new_urls_in_file(file_path):
    """
    Checks if a file contains any URLs.

    Args:
        file_path (str): The path to the file to check.

    Returns:
        bool: True if the file contains URLs, False otherwise.
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}", exc_info=True)
            return False

        # Read the file and check if it contains any non-empty lines
        with open(file_path, "r") as file:
            for line in file:
                if line.strip():  # Check for non-empty lines
                    return True

        # If no URLs are found
        return False
    except Exception as e:
        logging.error("An error occurred while checking the file.", exc_info=True)
        return False
```

### Usage Pattern

```python
# Check if there's work to do
if check_new_urls_in_file("data/urls_list.txt"):
    clean_urls = clean_file_new_urls("data/urls_list.txt")
    # Process clean_urls...
    append_to_existing_urls_in_db_file()
```

---

## Conclusions

### ✅ Good / Usable

1. **Deduplication pattern** - `list(set(items))`
2. **Inbox/processed pattern** - Clean workflow for batch processing
3. **In-place file cleanup** - Read, process, rewrite
4. **Early exit on empty** - Check before processing

### ⚠️ Limited / GitHub-Specific

1. **Hardcoded to GitHub URLs** - `https://github.com/` prefix
2. **No URL validation** - Just prefix check, not full URL parsing
3. **No batch size limit** - Processes entire file at once
4. **Simple error handling** - Just logs and returns False

### 🔧 Generalized Pattern for AutoBiz

```python
# Generic URL cleaner
def clean_urls(file_path, url_prefix=None, extract_path=False):
    """
    Generic URL cleaner with optional prefix filter.

    Args:
        file_path: Path to URL file
        url_prefix: Optional prefix to filter by (e.g., "https://example.com/")
        extract_path: If True, removes prefix from URLs

    Returns:
        list: Cleaned URLs or paths
    """
    with open(file_path, 'r') as f:
        urls = list(set(line.strip() for line in f if line.strip()))

    if url_prefix:
        urls = [u for u in urls if u.startswith(url_prefix)]
        if extract_path:
            urls = [u[len(url_prefix):] for u in urls]

    urls.sort()

    with open(file_path, 'w') as f:
        f.write('\n'.join(urls) + '\n')

    return urls
```

### 📊 Comparison Matrix

| Pattern | MarketIntel | SerpApi | Ollama-Rag |
|---------|-------------|---------|------------|
| URL Cleaning | No | No | Yes (GitHub) |
| Deduplication | get_or_insert (DB) | No | set() |
| Inbox Pattern | No | No | Yes |
| File Operations | No | No | Yes |

### 🎯 Fit for AutoBiz

- **Pattern useful** - Inbox/processed workflow
- **Needs generalization** - Remove GitHub-specific logic
- **Deduplication** - MarketIntel's get_or_insert is better for DB

---

## Files

- `/tmp/Ollama-Rag/utils.py:334-416` - URL handling utilities
