# Code Structure - Request History Feature

## File Organization

```
InteceptProxy/
├── intercept_proxy.py          # Main application (MODIFIED)
│   ├── RequestHistory          # NEW CLASS
│   ├── InterceptAddon          # MODIFIED (added history support)
│   └── ProxyGUI                # MODIFIED (added history tab)
│
├── test_history.py             # NEW FILE - History tests
├── HISTORY_GUIDE.md            # NEW FILE - User guide
├── UI_LAYOUT.md                # NEW FILE - Visual documentation
├── CHANGES_SUMMARY.md          # NEW FILE - This summary
│
├── README.md                   # UPDATED - Added history features
├── USAGE_GUIDE.md              # UPDATED - Added history section
│
└── (existing files unchanged)
    ├── test_intercept.py
    ├── requirements.txt
    ├── run_proxy_headless.py
    └── ...
```

## Class Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    InterceptConfig                          │
│  (Unchanged - manages interception rules)                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    RequestHistory                           │
│  (NEW - manages request history)                            │
│                                                              │
│  + history: list                                            │
│  + max_items: int                                           │
│                                                              │
│  + add_request(flow: HTTPFlow)                              │
│  + get_history() → list                                     │
│  + clear_history()                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    InterceptAddon                           │
│  (MODIFIED - added history tracking)                        │
│                                                              │
│  + config: InterceptConfig                                  │
│  + history: RequestHistory (NEW)                            │
│                                                              │
│  + request(flow: HTTPFlow)                                  │
│  + response(flow: HTTPFlow) (NEW)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ProxyGUI                                 │
│  (MODIFIED - added history tab and UI)                      │
│                                                              │
│  + config: InterceptConfig                                  │
│  + history: RequestHistory (NEW)                            │
│  + notebook: ttk.Notebook (NEW)                             │
│  + history_tree: ttk.Treeview (NEW)                         │
│  + details_notebook: ttk.Notebook (NEW)                     │
│                                                              │
│  + setup_ui()                                               │
│  + setup_rules_tab() (NEW)                                  │
│  + setup_history_tab() (NEW)                                │
│  + update_history_list() (NEW)                              │
│  + apply_history_filter() (NEW)                             │
│  + show_request_details() (NEW)                             │
│  + clear_history() (NEW)                                    │
│  + (existing methods...)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Method Call Flow

### Capturing Requests

```
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │ HTTP Request
       ▼
┌──────────────┐
│ mitmproxy    │
└──────┬───────┘
       │ calls addon
       ▼
┌───────────────────────────────────┐
│ InterceptAddon.request(flow)      │
│ - Applies interception rules      │
│ - Modifies parameters if needed   │
└───────────────┬───────────────────┘
                │
                ▼
┌──────────────┐
│   Server     │
└──────┬───────┘
       │ HTTP Response
       ▼
┌──────────────┐
│ mitmproxy    │
└──────┬───────┘
       │ calls addon
       ▼
┌───────────────────────────────────┐
│ InterceptAddon.response(flow)     │
│ - Stores request+response         │
│   in RequestHistory               │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ RequestHistory.add_request(flow)  │
│ - Extracts data                   │
│ - Adds to history list            │
│ - Enforces size limit             │
└───────────────────────────────────┘
```

### Displaying History

```
┌───────────────────────────────────┐
│ ProxyGUI.update_history_list()    │
│ - Called every 1 second           │
│ - Triggers filter application     │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ ProxyGUI.apply_history_filter()   │
│ - Gets current filter values      │
│ - Iterates through history        │
│ - Applies method filter           │
│ - Applies regex domain filter     │
│ - Updates UI (Treeview)           │
└───────────────────────────────────┘
```

### Showing Details

```
┌───────────────────────────────────┐
│ User clicks on history item       │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ Treeview <<TreeviewSelect>> event │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ ProxyGUI.show_request_details()   │
│ - Gets selected item              │
│ - Finds matching history entry    │
│ - Formats request info            │
│ - Updates request_text widget     │
│ - Formats response info           │
│ - Updates response_text widget    │
└───────────────────────────────────┘
```

## Key Code Snippets

### 1. RequestHistory.add_request()

```python
def add_request(self, flow: http.HTTPFlow):
    request = flow.request
    response = flow.response
    
    entry = {
        'timestamp': datetime.now(),
        'host': request.pretty_host,
        'method': request.method,
        'url': request.pretty_url,
        'path': request.path,
        'status': response.status_code if response else 0,
        'request_headers': dict(request.headers),
        'request_body': request.content.decode('utf-8', errors='ignore'),
        'response_headers': dict(response.headers) if response else {},
        'response_body': response.content.decode('utf-8', errors='ignore'),
    }
    
    self.history.append(entry)
    
    if len(self.history) > self.max_items:
        self.history.pop(0)
```

### 2. Filter Application

```python
def apply_history_filter(self):
    # Clear current display
    for item in self.history_tree.get_children():
        self.history_tree.delete(item)
    
    # Get filter values
    method_filter = self.method_filter.get()
    domain_pattern = self.domain_filter_entry.get().strip()
    
    # Compile regex
    domain_regex = None
    if domain_pattern:
        try:
            domain_regex = re.compile(domain_pattern, re.IGNORECASE)
        except re.error:
            domain_regex = None
    
    # Filter and display
    for entry in self.history.get_history():
        # Apply filters
        if method_filter != "Todos" and entry['method'] != method_filter:
            continue
        if domain_regex and not domain_regex.search(entry['host']):
            continue
        
        # Add to display
        date_str = entry['timestamp'].strftime('%d/%m/%Y')
        time_str = entry['timestamp'].strftime('%H:%M:%S')
        self.history_tree.insert('', 'end', 
                                values=(entry['host'], date_str, time_str, 
                                       entry['method'], entry['status'], entry['url']))
```

### 3. Auto-refresh

```python
def update_history_list(self):
    self.apply_history_filter()
    # Schedule next update in 1 second
    self.root.after(1000, self.update_history_list)
```

### 4. Detail Display

```python
def show_request_details(self, event):
    selection = self.history_tree.selection()
    if not selection:
        return
    
    # Find the entry
    item = selection[0]
    values = self.history_tree.item(item)['values']
    selected_entry = # ... find matching entry ...
    
    # Format request
    request_info = f"URL: {selected_entry['url']}\n"
    request_info += f"Método: {selected_entry['method']}\n"
    # ... add headers and body ...
    
    self.request_text.delete('1.0', tk.END)
    self.request_text.insert('1.0', request_info)
    
    # Format response
    response_info = f"Status: {selected_entry['status']}\n"
    # ... add headers and body ...
    
    self.response_text.delete('1.0', tk.END)
    self.response_text.insert('1.0', response_info)
```

## Data Structures

### History Entry

```python
{
    'timestamp': datetime.datetime(2025, 1, 15, 14, 30, 15),
    'host': 'exemplo.com',
    'method': 'GET',
    'url': 'http://exemplo.com/contato?Titulo=teste1',
    'path': '/contato',
    'status': 200,
    'request_headers': {
        'User-Agent': 'Mozilla/5.0...',
        'Accept': 'text/html...',
        # ...
    },
    'request_body': 'Titulo=teste1&Nome=Joao',
    'response_headers': {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Length': '1234',
        # ...
    },
    'response_body': '<!DOCTYPE html>...'
}
```

## UI Widget Hierarchy

```
root (Tk)
├── control_frame (LabelFrame) "Controle do Proxy"
│   ├── status_label (Label)
│   ├── start_button (Button)
│   ├── stop_button (Button)
│   └── port_label (Label)
│
└── notebook (Notebook)
    ├── rules_tab (Frame) "Regras de Interceptação"
    │   ├── config_frame (LabelFrame)
    │   │   └── (entry fields and buttons)
    │   ├── list_frame (LabelFrame)
    │   │   └── rules_tree (Treeview)
    │   └── buttons_frame (Frame)
    │
    └── history_tab (Frame) "Histórico de Requisições"
        ├── filter_frame (LabelFrame)
        │   ├── method_filter (Combobox)
        │   ├── domain_filter_entry (Entry)
        │   └── (buttons)
        │
        └── paned (PanedWindow)
            ├── list_frame (LabelFrame)
            │   └── history_tree (Treeview)
            │
            └── details_frame (LabelFrame)
                └── details_notebook (Notebook)
                    ├── request_tab (Frame)
                    │   └── request_text (ScrolledText)
                    │
                    └── response_tab (Frame)
                        └── response_text (ScrolledText)
```

## Integration Points

### With mitmproxy

```python
# When used as mitmproxy addon
addons = []
if __name__ != "__main__":
    config = InterceptConfig()
    history = RequestHistory()  # NEW
    addons = [InterceptAddon(config, history)]  # MODIFIED
```

### With GUI

```python
class ProxyGUI:
    def __init__(self):
        self.config = InterceptConfig()
        self.history = RequestHistory()  # NEW
        # ...
    
    def start_proxy(self):
        def run_proxy():
            addon = InterceptAddon(self.config, self.history)  # MODIFIED
            mitmdump([...])
        # ...
```

## Performance Characteristics

### Memory Usage
- O(n) where n = number of entries (max 1000)
- Each entry: ~2-10 KB (depends on request/response size)
- Total max: ~10 MB

### CPU Usage
- Filter application: O(n) per second
- Regex matching: O(m) per entry (m = domain length)
- UI updates: O(k) where k = filtered results

### Time Complexity
- Add entry: O(1)
- Clear history: O(1)
- Apply filter: O(n)
- Show details: O(n) worst case (find entry)

## Error Handling

### Regex Filter
```python
try:
    domain_regex = re.compile(domain_pattern, re.IGNORECASE)
except re.error:
    domain_regex = None  # Ignore invalid regex
```

### Request/Response Decoding
```python
request.content.decode('utf-8', errors='ignore')
# Gracefully handles non-UTF8 content
```

### Missing Response
```python
response.status_code if response else 0
# Handles requests without responses
```
