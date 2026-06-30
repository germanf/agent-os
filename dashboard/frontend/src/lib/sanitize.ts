import DOMPurify from 'dompurify';
import { marked } from 'marked';

/**
 * Configuration for DOMPurify to allow safe Markdown-rendered HTML
 * while preventing XSS attacks
 */
const SANITIZE_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 'del', 'code', 'pre',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'a', 'blockquote', 'hr', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
  ],
  ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class', 'data-target'],
  RETURN_DOM: false,
  RETURN_DOM_FRAGMENT: false,
  FORCE_BODY: false,
  SANITIZE_DOM: true,
} as Parameters<typeof DOMPurify.sanitize>[1];

/**
 * Force rel="noopener noreferrer" on any <a target="_blank"> that survives
 * sanitization, to prevent tabnabbing (see issue #107). Registered once at
 * module load time so it isn't re-added on every sanitize call.
 */
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.getAttribute('target') === '_blank') {
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

/**
 * Parse Markdown and sanitize the resulting HTML to prevent XSS
 * @param markdown - The Markdown text to parse
 * @param markdownOptions - Options to pass to marked.parse()
 * @returns Sanitized HTML string
 */
export function parseAndSanitize(
  markdown: string,
  markdownOptions?: Parameters<typeof marked.parse>[1],
): string {
  const html = marked.parse(markdown, { async: false, ...markdownOptions }) as string;
  return DOMPurify.sanitize(html, SANITIZE_CONFIG);
}

/**
 * Sanitize already-rendered HTML to prevent XSS
 * @param html - The HTML string to sanitize
 * @returns Sanitized HTML string
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, SANITIZE_CONFIG);
}
