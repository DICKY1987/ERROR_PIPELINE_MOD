# Technical Architecture Documentation

## System Overview

The Validation Pipeline is a deterministic, plugin-based file validation system built with Python 3.9+. It features incremental validation, DAG-based plugin ordering, and atomic operations for production reliability.

## Core Design Principles

### 1. Determinism
Every validation run must produce identical results given identical inputs:
- Environment scrubbing (remove proxy settings, set locale to C)
- Tool version capture and verification
- Content-based hashing (SHA-256) for change detection
- No network access during validation
- Stable plugin ordering via topological sort

### 2. Isolation
Never modify original files, maintain clean separation:
- Work in `tempfile.TemporaryDirectory()` per file
- Copy original → validate → copy to output
- Each plugin execution is stateless
- Output naming: `{stem}_VALIDATED_{timestamp}_{runid}{ext}`

### 3. Atomicity
Operations complete fully or not at all:
- JSONL rotation: temp file write → atomic `os.replace()`
- Hash cache: JSON write with proper error handling
- Plugin execution: timeout + exception handling

### 4. Reproducibility
Track everything needed to reproduce results:
- Run ID (ULID): sortable, unique identifier
- Toolchain versions captured in every report
- Timestamp in UTC (ISO 8601 format)
- Complete plugin execution metadata

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     GUI Layer                           │
│  (ValidationPipelineGUI + Threading)                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                Pipeline Engine                          │
│  • Incremental validation (FileHashCache)               │
│  • Temp directory isolation                             │
│  • Report generation (JSON + JSONL)                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│               Plugin Manager                            │
│  • Auto-discovery from src/plugins/                     │
│  • DAG ordering (graphlib.TopologicalSorter)           │
│  • Dependency resolution                                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│               Plugin Instances                          │
│  • BasePlugin subclasses                                │
│  • Tool execution (subprocess, no shell)                │
│  • Output parsing (tool-specific)                       │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Single File Processing

```
1. GUI: User drops file
   ↓
2. PipelineEngine.process_file(file_path)
   ↓
3. Generate ULID run_id
   ↓
4. FileHashCache.has_changed(file_path)?
   ├─ No → Return {"status": "skipped"}
   └─ Yes → Continue
   ↓
5. Create tempfile.TemporaryDirectory()
   ↓
6. shutil.copy2(original → temp_file)
   ↓
7. PluginManager.get_plugins_for_file(temp_file)
   ├─ Filter by file extension
   ├─ Build dependency graph from "requires"
   └─ TopologicalSorter.static_order()
   ↓
8. For each plugin in order:
   ├─ plugin.build_command(temp_file)
   ├─ Inject fix_args if auto_fix enabled
   ├─ subprocess.run(cmd, env=scrubbed_env, shell=False)
   ├─ plugin.parse_output() → ValidationErrors
   └─ Collect errors
   ↓
9. shutil.copy2(temp_file → output_folder/validated_name)
   ↓
10. Generate report JSON with toolchain versions
    ↓
11. Save individual report: {output_file}.json
    ↓
12. JSONLManager.append() → pipeline_errors.jsonl
    ↓
13. FileHashCache.mark_validated() + save cache
    ↓
14. Return report dict
```

## Plugin System

### Discovery Mechanism

```python
# PluginManager._discover_plugins()
for plugin_dir in plugins_dir.iterdir():
    if not plugin_dir.is_dir(): continue
    
    manifest = plugin_dir / 'manifest.json'
    plugin_py = plugin_dir / 'plugin.py'
    
    if not (manifest.exists() and plugin_py.exists()): continue
    
    # Dynamically import
    spec = importlib.util.spec_from_file_location(...)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Call register() to get instance
    plugin = module.register()
    
    # Verify tool availability
    if plugin.check_tool_available():
        self.plugins[plugin.plugin_id] = plugin
```

### DAG Ordering

```python
# Build dependency graph
graph = {}
for plugin in applicable_plugins:
    deps = plugin.manifest.get('requires', [])
    graph[plugin.plugin_id] = deps

# Topological sort
sorter = TopologicalSorter(graph)
sorted_ids = list(sorter.static_order())

# Example:
# graph = {
#   'python_black': [],
#   'python_ruff': ['python_black']
# }
# Result: ['python_black', 'python_ruff']
```

### Plugin Execution

```python
# BasePlugin.execute()
cmd = self.build_command(file_path)

# Inject fix args
if self.auto_fix and 'fix_args' in self.manifest['tool']:
    fix_args = self.manifest['tool']['fix_args']
    cmd = cmd[:-1] + fix_args + [cmd[-1]]

# Scrub environment
env = os.environ.copy()
env['LC_ALL'] = 'C'
env['LANG'] = 'C'
env.pop('PYTHONPATH', None)
for key in list(env.keys()):
    if key.upper().endswith('_PROXY'):
        env.pop(key)

# Execute with timeout
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=120,
    cwd=file_path.parent,
    env=env,
    shell=False  # NEVER use shell=True
)

# Check success code map
allowed_codes = set(self.manifest['tool'].get('success_codes', [0]))
success = result.returncode in allowed_codes
```

## Incremental Validation

### Hash-Based Change Detection

```python
# FileHashCache.has_changed()
current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
cached_entry = self.cache.get(str(file_path.absolute()))

if not cached_entry or cached_entry['hash'] != current_hash:
    self.cache[file_key] = {
        'hash': current_hash,
        'last_validated': datetime.now(timezone.utc).isoformat()
    }
    return True  # File changed or new

return False  # File unchanged
```

### Cache Structure

```json
{
  "/absolute/path/to/file.py": {
    "hash": "a1b2c3...",
    "last_validated": "2025-11-02T18:30:45Z",
    "had_errors": false
  }
}
```

## JSONL Rotation (75KB Limit)

### Atomic Rotation Algorithm

```python
# JSONLManager._rotate_if_needed()
if file_size <= 75KB: return

# Read from end, keep newest lines
with open(path, 'rb') as f:
    f.seek(0, os.SEEK_END)
    buffer = []
    pos = f.tell()
    
    while pos > 0 and total < 75KB:
        step = min(8192, pos)
        pos -= step
        f.seek(pos)
        buffer.append(f.read(step))

# Parse lines, keep from tail
lines = decode(reversed(buffer)).splitlines()
keep_lines = []
total = 0

for line in reversed(lines):
    size = len(line.encode('utf-8')) + 1
    if total + size > 75KB: break
    keep_lines.append(line)
    total += size

# Atomic rewrite
tmp = tempfile.mkstemp(dir=parent, prefix='.tmp_', suffix='.jsonl')
write_lines(tmp, reversed(keep_lines))
os.replace(tmp, original_path)
```

## Report Format

### Per-File JSON Report

```json
{
  "run_id": "01JB4C3GY7KQWX2VMRT8HSDFGH",
  "file_in": "C:/original/test.py",
  "file_out": "D:/output/test_VALIDATED_20251102_183045_01JB4C.py",
  "timestamp_utc": "2025-11-02T18:30:45.123456Z",
  "toolchain": {
    "python_black": "Black, 24.8.0",
    "python_ruff": "ruff 0.6.9"
  },
  "summary": {
    "plugins_run": 2,
    "total_errors": 1,
    "total_warnings": 3,
    "auto_fixed": 5
  },
  "plugin_results": [
    {
      "plugin_id": "python_black",
      "name": "Black Formatter",
      "duration_s": 0.42,
      "auto_fixed": 3,
      "errors": [
        {
          "tool": "black",
          "severity": "info",
          "file": "test.py",
          "line": null,
          "column": null,
          "code": null,
          "message": "File reformatted to Black style",
          "auto_fixed": true
        }
      ]
    },
    {
      "plugin_id": "python_ruff",
      "name": "Ruff Linter",
      "duration_s": 0.55,
      "auto_fixed": 2,
      "errors": [
        {
          "tool": "ruff",
          "severity": "warning",
          "file": "test.py",
          "line": 12,
          "column": 5,
          "code": "F401",
          "message": "module imported but unused",
          "auto_fixed": false
        }
      ]
    }
  ]
}
```

### JSONL Aggregate Entry

```json
{"run_id":"01JB4C","file_out":"test_VALIDATED_20251102_183045_01JB4C.py","tool":"ruff","severity":"warning","code":"F401","line":12,"message":"module imported but unused","auto_fixed":false,"ts":"2025-11-02T18:30:45Z"}
```

## Threading Model

### GUI Thread Safety

```python
class ValidationPipelineGUI:
    def process_files(self):
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()
    
    def _process_thread(self):
        # Disable button
        self.process_btn.config(state=tk.DISABLED)
        
        # Run pipeline (blocking)
        results = self.pipeline_engine.process_files(self.selected_files)
        
        # Update UI (thread-safe via Tkinter)
        self.log("Complete!")
        
        # Re-enable button
        self.process_btn.config(state=tk.NORMAL)
```

### Concurrency Notes

- Current: Sequential file processing
- Future: Parallel file processing via `concurrent.futures.ThreadPoolExecutor`
- JSONL writes would need locking: `threading.Lock()` around `append()`

## Error Handling

### Plugin Execution Failures

```python
try:
    result = subprocess.run(cmd, timeout=120, ...)
    errors = self.parse_output(...)
except subprocess.TimeoutExpired:
    return PluginResult(
        success=False,
        errors=[ValidationError(
            tool=self.name,
            severity='error',
            message='Plugin execution timeout'
        )]
    )
except Exception as e:
    return PluginResult(
        success=False,
        errors=[ValidationError(
            tool=self.name,
            severity='error',
            message=f'Plugin failed: {e}'
        )]
    )
```

### Graceful Degradation

- Plugin tool unavailable → Skip plugin, log warning
- Plugin crashes → Capture error, continue with remaining plugins
- File unreadable → Skip file, log error
- Output folder permission denied → Show error dialog

## Performance Optimizations

### 1. Incremental Validation
- **Benefit**: Skip unchanged files entirely
- **Cost**: SHA-256 hash computation (< 10ms for typical files)
- **Cache size**: ~200 bytes per file

### 2. Temp Directory Reuse
- Each file gets fresh temp dir (isolation)
- Automatic cleanup via context manager
- OS-level temp space management

### 3. Plugin Ordering
- DAG ensures minimal re-runs
- Auto-fix plugins run first (e.g., Black before Ruff)
- Dependent plugins only if prerequisites pass

## Security Considerations

### 1. Command Injection Prevention
```python
# ✅ SAFE: List form, no shell
subprocess.run(['tool', '--arg', file_path], shell=False)

# ❌ UNSAFE: String form with shell
subprocess.run(f'tool --arg {file_path}', shell=True)
```

### 2. Path Traversal Prevention
```python
# Resolve symlinks and check parent
file_path = Path(file_path).resolve()
if not file_path.is_file():
    raise ValueError("Invalid file path")
```

### 3. Resource Limits
- Timeout: 120s per plugin execution
- Max files: 10 per batch
- Max JSONL size: 75KB (auto-rotation)

## Extension Points

### Adding New File Types

1. Create plugin folder: `src/plugins/my_validator/`
2. Add manifest with `file_extensions: [".ext"]`
3. Implement plugin class
4. Automatic discovery on next run

### Custom GUI Themes

```python
# src/gui/main_window.py
from tkinter import ttk

style = ttk.Style()
style.theme_use('clam')  # or 'alt', 'default', 'classic'
```

### Alternative Storage

```python
# Replace JSONLManager with:
class DatabaseManager:
    def append(self, record):
        self.db.insert(record)
```

## Testing Strategy

### Unit Tests (Future)
```python
def test_plugin_ordering():
    graph = {'b': ['a'], 'c': ['b']}
    result = topological_sort(graph)
    assert result == ['a', 'b', 'c']

def test_incremental_cache():
    cache = FileHashCache(Path('test.json'))
    assert cache.has_changed(Path('file.txt')) == True
    assert cache.has_changed(Path('file.txt')) == False
```

### Integration Tests
```bash
# test_cli.py provides basic integration test
python test_cli.py
```

### Golden File Tests
```python
# Compare output byte-for-byte
output = validate('input.py')
assert output == Path('expected_output.py').read_bytes()
```

## Deployment

### Standalone Executable (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### Docker Container
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## Monitoring & Observability

### Logging Levels
- DEBUG: Plugin discovery, cache hits/misses
- INFO: File processing, plugin execution
- WARNING: Plugin unavailable, tool errors
- ERROR: Pipeline failures, crashes

### Metrics (Future)
- Files processed per minute
- Cache hit rate
- Plugin execution time distribution
- Error rate by plugin

## Known Limitations

1. **Sequential Processing**: Files validated one-at-a-time
2. **GUI Single-threaded**: One validation batch at a time
3. **No Undo**: Validated files overwrite (use version control)
4. **Windows-only GUI**: Uses tkinterdnd2 (Windows-optimized)

## Future Enhancements

1. **Parallel Processing**: ThreadPoolExecutor for multi-file
2. **Plugin Marketplace**: Download plugins from registry
3. **Watch Mode**: Auto-validate on file save
4. **CI/CD Integration**: GitHub Actions / Azure Pipelines
5. **Plugin Conflict Detection**: Warn if plugins modify same aspects
6. **Dry-run Mode**: Preview changes without applying

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-02  
**Maintainer**: Pipeline Team
