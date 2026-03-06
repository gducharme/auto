## Safari JS fixture integration

Validate that replay JavaScript helpers can run through the AppleScript-driven
Safari controller against saved HTML fixtures.

```json
{
  "title": "safari_js_integration",
  "description": "Open local fixture HTML in Safari and run replay helper JS via run_js",
  "inputs": {
    "fixture_html": {
      "type": "string",
      "description": "Absolute path to a saved HTML fixture file"
    },
    "js_files": {
      "type": "array",
      "description": "JavaScript helper files to inject and execute"
    }
  },
  "assertions": [
    "SafariController can open a file:// URL",
    "Injected helper functions execute without script errors",
    "DOM side-effects from helper functions are observable via run_js"
  ]
}
```
