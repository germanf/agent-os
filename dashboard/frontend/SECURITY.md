# Security Implementation: XSS Prevention with DOMPurify

## Overview

This document describes the XSS (Cross-Site Scripting) prevention mechanisms implemented in the Twitter Exporter Dashboard frontend.

## XSS Vulnerability Context

When rendering user-generated or untrusted Markdown content (especially in chat messages and notes), the application could be vulnerable to XSS attacks if the HTML output is not properly sanitized.

### Examples of XSS Payloads

```markdown
[click me](javascript:alert('XSS'))
<img src=x onerror="fetch('/api/chat/send?msg=pwned')">
<script>console.log('XSS')</script>
```

## Solution: DOMPurify + marked.parse()

We use two libraries together to safely render Markdown:

1. **marked** - Parses Markdown to HTML (vulnerable to XSS if output is not sanitized)
2. **DOMPurify** - Sanitizes HTML to remove dangerous attributes and tags

### Implementation Pattern

```typescript
import { parseAndSanitize, sanitizeHtml } from '../lib/sanitize';

// For Markdown content:
const sanitizedHtml = parseAndSanitize(markdownText);

// For already-rendered HTML:
const sanitizedHtml = sanitizeHtml(htmlString);

// Use in React with dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
```

## Sanitization Configuration

DOMPurify is configured with a whitelist approach:

### Allowed Tags

- **Text formatting**: `<p>`, `<strong>`, `<em>`, `<u>`, `<del>`, `<code>`, `<pre>`
- **Headings**: `<h1>` through `<h6>`
- **Lists**: `<ul>`, `<ol>`, `<li>`
- **Links**: `<a>` (only with `href`, `title`, `target`, `rel`, `class`, `data-target`)
- **Tables**: `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`, `<th>`
- **Other**: `<br>`, `<blockquote>`, `<hr>`

### Allowed Attributes

- `href` - For links
- `title` - For tooltips
- `target` - For link targets (e.g., `_blank`)
- `rel` - For link relationships (e.g., `noopener`)
- `class` - For CSS styling
- `data-target` - For internal wiki links in notes

### Blocked

- Event handlers: `onclick`, `onerror`, `onload`, etc.
- Dangerous protocols: `javascript:`, `data:` (without proper MIME type)
- Dangerous tags: `<script>`, `<iframe>`, `<object>`, etc.

## Components Updated

### 1. `ChatBubbleAssistant.tsx`

Renders assistant responses from Claude with Markdown formatting:

```typescript
import { parseAndSanitize } from '../lib/sanitize';

const sanitizedHtml = parseAndSanitize(text);

<div
  className="chat-bubble assistant"
  dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
/>
```

**Before**: `marked.parse()` output was used directly  
**After**: `parseAndSanitize()` wraps `marked.parse()` with DOMPurify sanitization

### 2. `Notes.tsx`

Renders Markdown notes from the Obsidian vault:

```typescript
import { parseAndSanitize, sanitizeHtml } from '../lib/sanitize';

const resolved = resolveWikilinks(content, byPath, byBasename);
const sanitized = sanitizeHtml(await parseAndSanitize(resolved));
setHtml(sanitized);

<div
  onClick={handleContentClick}
  dangerouslySetInnerHTML={{ __html: html }}
/>
```

**Before**: `marked.parse()` output was used directly  
**After**: Two-stage sanitization to handle both Markdown and wikilink HTML

### 3. `sanitize.ts` (New)

Helper module with sanitization functions:

- `parseAndSanitize(markdown: string): string` - Parse Markdown and sanitize output
- `sanitizeHtml(html: string): string` - Sanitize already-rendered HTML

## Testing

### Unit Tests

Test suite at `src/lib/__tests__/sanitize.test.ts` validates:

1. **XSS Prevention**
   - Script tags removed
   - Event handlers stripped
   - `javascript:` URLs blocked

2. **Safe Content Preservation**
   - Markdown formatting preserved (`**bold**`, `*italic*`)
   - Links with safe URLs allowed
   - Code blocks rendered
   - Headers and lists rendered
   - Wikilinks (with `data-target`) preserved

3. **Edge Cases**
   - Empty strings handled
   - Deeply nested dangerous attributes removed
   - Class attributes for styling preserved

#### Running Tests

In browser console (after build):

```javascript
import { runSanitizationTests } from './lib/__tests__/sanitize.test.ts';
await runSanitizationTests();
```

## Important Notes

### Client-Side Only

DOMPurify provides **client-side** XSS protection. For defense in depth:

- **Validate on backend**: Don't trust client-side sanitization alone
- **Content Security Policy (CSP)**: Set strict CSP headers in `nginx.conf` to prevent inline scripts
- **HTTPS**: Always use HTTPS to prevent MITM attacks that could inject malicious code

### Autofirmados vs Let's Encrypt

This implementation uses autofirmed certificates for HTTPS. When upgrading to Let's Encrypt:

- HSTS headers (already in place) will be respected by browsers
- Client-side XSS protection remains unchanged
- Backend validation should still be implemented

### Performance Impact

- DOMPurify sanitization adds ~1-5ms per message (negligible for user experience)
- Sanitization happens synchronously on the main thread
- For large documents (>100KB), consider lazy rendering

## Future Improvements

1. **Content Security Policy (CSP)**
   - Add CSP headers in nginx to prevent inline script execution
   - Reference: `DEPLOYMENT.md` (nginx configuration section)

2. **Backend Validation**
   - Implement server-side sanitization/validation in `dashboard/main.py`
   - Validate Markdown input before storing/processing

3. **Stricter Sandbox**
   - Consider rendering Markdown in a Web Worker or iframe for additional isolation

4. **Markdown Sanitization Hooks**
   - Configure marked library hooks to escape dangerous constructs before sanitization

## References

- [DOMPurify Documentation](https://github.com/cure53/DOMPurify)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [MDN Web Docs: dangerouslySetInnerHTML](https://react.dev/reference/react-dom/dangerouslySetInnerHTML)
- [RFC 6797: HTTP Strict Transport Security](https://tools.ietf.org/html/rfc6797)
