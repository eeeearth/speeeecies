// dom.js — a tiny safe DOM-construction helper, shared by the site's pages.
//
// Species, behaviour and schema data all come from the public repo (open to
// contributor PRs) or from the previewer's paste box, so every string in it
// is untrusted. Never build markup by interpolating such strings into an
// innerHTML template — use `el()` (or plain createElement/textContent)
// instead, which only ever sets text nodes and attribute values, never
// parses anything as HTML.
//
// el(tag, props, ...children)
//   props: an object of attributes/properties, or null/undefined.
//     - "class" sets className.
//     - a value of null/undefined/false skips the attribute.
//     - anything else is set with setAttribute (never innerHTML).
//   children: strings/numbers become text nodes; DOM nodes are appended
//     as-is; null/undefined/false are skipped. Arrays are flattened.
export function el(tag, props, ...children) {
  const node = document.createElement(tag);
  if (props) {
    for (const [key, value] of Object.entries(props)) {
      if (value == null || value === false) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    }
  }
  appendChildren(node, children);
  return node;
}

function appendChildren(node, children) {
  for (const child of children) {
    if (child == null || child === false) continue;
    if (Array.isArray(child)) {
      appendChildren(node, child);
    } else if (child instanceof Node) {
      node.appendChild(child);
    } else {
      node.appendChild(document.createTextNode(String(child)));
    }
  }
}

// A safe relative href for a path segment that may contain untrusted
// characters (e.g. a species slug read from data). Always builds the URL
// from a fixed prefix/suffix with the untrusted part percent-encoded, so it
// can never smuggle in a `javascript:` scheme or break out of the attribute.
export function safeHref(prefix, untrustedSegment, suffix = "") {
  return `${prefix}${encodeURIComponent(untrustedSegment)}${suffix}`;
}
