import { describe, it, expect } from 'vitest';
import { parseAndSanitize, sanitizeHtml } from '../sanitize';

describe('DOMPurify Sanitization', () => {
  it('removes script tags from HTML', () => {
    const test = '<p>Hello</p><script>alert("XSS")</script>';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('<script>');
    expect(result).toContain('Hello');
  });

  it('removes onerror handlers from img tags', () => {
    const test = '<img src=x onerror="alert(\'XSS\')">';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('onerror');
  });

  it('removes onclick handlers', () => {
    const test = '<div onclick="fetch(\'/api/steal\')">Click me</div>';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('onclick');
  });

  it('removes javascript: URLs from links', () => {
    const test = '<a href="javascript:alert(\'XSS\')">click</a>';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('javascript:');
  });

  it('allows safe HTML tags', () => {
    const test = '<p>Paragraph</p><strong>Bold</strong><em>Italic</em>';
    const result = sanitizeHtml(test);
    expect(result).toContain('<p>');
    expect(result).toContain('<strong>');
    expect(result).toContain('<em>');
  });

  it('preserves href attribute', () => {
    const test = '<a href="https://example.com">link</a>';
    const result = sanitizeHtml(test);
    expect(result).toContain('href=');
    expect(result).toContain('example.com');
  });

  it('preserves data-target for wikilinks', () => {
    const test = '<a class="wikilink" href="#" data-target="/path/to/note">Note</a>';
    const result = sanitizeHtml(test);
    expect(result).toContain('data-target=');
    expect(result).toContain('/path/to/note');
  });

  it('allows code and pre tags', () => {
    const test = '<pre><code>const x = 1;</code></pre>';
    const result = sanitizeHtml(test);
    expect(result).toContain('<pre>');
    expect(result).toContain('<code>');
  });

  it('prevents XSS via javascript: URL in markdown', () => {
    const test = '[click me](javascript:alert("XSS"))';
    const result = parseAndSanitize(test);
    expect(result).not.toContain('javascript:');
  });

  it('allows bold markdown formatting', () => {
    const test = '**bold** and *italic*';
    const result = parseAndSanitize(test);
    expect(result).toContain('<strong>');
    expect(result).toContain('<em>');
  });

  it('allows safe URLs in markdown links', () => {
    const test = '[GitHub](https://github.com)';
    const result = parseAndSanitize(test);
    expect(result).toContain('https://github.com');
  });

  it('allows headers in markdown', () => {
    const test = '# Header 1\n## Header 2';
    const result = parseAndSanitize(test);
    expect(result).toContain('<h1>');
    expect(result).toContain('<h2>');
  });

  it('allows unordered lists in markdown', () => {
    const test = '- Item 1\n- Item 2';
    const result = parseAndSanitize(test);
    expect(result).toContain('<ul>');
    expect(result).toContain('<li>');
  });

  it('allows code blocks in markdown', () => {
    const test = '```\nconst x = 1;\n```';
    const result = parseAndSanitize(test);
    expect(result).toContain('<code>');
  });

  it('handles empty string in parseAndSanitize', () => {
    expect(parseAndSanitize('')).toBe('');
  });

  it('handles empty string in sanitizeHtml', () => {
    expect(sanitizeHtml('')).toBe('');
  });

  it('removes deeply nested onclick handlers', () => {
    const test = '<div><p><span onclick="bad()">text</span></p></div>';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('onclick');
  });

  it('preserves class attribute for styling', () => {
    const test = '<div class="container"><p class="text">Content</p></div>';
    const result = sanitizeHtml(test);
    expect(result).toContain('class=');
  });

  it('forces rel="noopener noreferrer" on links with target="_blank"', () => {
    const test = '<a href="https://example.com" target="_blank">link</a>';
    const result = sanitizeHtml(test);
    expect(result).toContain('rel="noopener noreferrer"');
  });

  it('does not add a rel attribute to links without target="_blank"', () => {
    const test = '<a href="https://example.com">link</a>';
    const result = sanitizeHtml(test);
    expect(result).not.toContain('rel=');
  });
});
