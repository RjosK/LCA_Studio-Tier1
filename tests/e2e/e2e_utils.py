"""
ECONODE E2E Test Suite - Shared Utilities & Fixtures (e2e_utils.py)
Provides zero-dependency HTTP client, DOM parser, CSS tokenizer, and i18n validator.
"""

import os
import re
import json
import urllib.request
import urllib.error
from html.parser import HTMLParser

# Server configuration
DEFAULT_BASE_URL = os.environ.get("ECONODE_SERVER_URL", "http://127.0.0.1:8095")
WORKSPACE_PUBLIC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "public")
)


def fetch_resource(url_path, base_url=DEFAULT_BASE_URL, timeout=5.0):
    """
    Fetches a resource from the live server.
    Falls back to local public/ directory if server is unreachable.
    Returns (status_code, headers_dict, content_str).
    """
    if not url_path.startswith("/"):
        url_path = "/" + url_path

    full_url = base_url.rstrip("/") + url_path
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "EconodeE2ETestRunner/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            headers = {k.lower(): v for k, v in response.getheaders()}
            content = response.read().decode("utf-8", errors="replace")
            return status, headers, content
    except Exception as exc:
        # Fallback to local files in workspace if server offline
        local_path = os.path.join(WORKSPACE_PUBLIC_DIR, url_path.lstrip("/"))
        if url_path == "/" or url_path == "/index.html":
            local_path = os.path.join(WORKSPACE_PUBLIC_DIR, "index.html")
        
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return 200, {"content-type": "text/html; charset=utf-8", "x-fallback": "true"}, content
        raise RuntimeError(f"Unable to fetch {full_url} and local file {local_path} not found: {exc}")


class DOMElement:
    """Represents a lightweight parsed DOM node with tag, attributes, and text."""
    def __init__(self, tag, attrs=None):
        self.tag = tag.lower()
        self.attrs = {k.lower(): v for k, v in (attrs or [])}
        self.children = []
        self.text_content = ""
        self.parent = None

    @property
    def element_id(self):
        return self.attrs.get("id", "")

    @property
    def classes(self):
        cls = self.attrs.get("class", "")
        return cls.split() if cls else []

    def get_full_text(self):
        """Recursively retrieves all text content from element and descendants."""
        parts = [self.text_content] if self.text_content else []
        for child in self.children:
            child_txt = child.get_full_text()
            if child_txt:
                parts.append(child_txt)
        return " ".join(parts).strip()

    @property
    def full_text(self):
        return self.get_full_text()

    def get_attr(self, name, default=None):
        return self.attrs.get(name.lower(), default)

    def has_class(self, class_name):
        return class_name in self.classes

    def find_by_id(self, target_id):
        if self.element_id == target_id:
            return self
        for child in self.children:
            found = child.find_by_id(target_id)
            if found:
                return found
        return None

    def find_all_by_class(self, class_name):
        results = []
        if self.has_class(class_name):
            results.append(self)
        for child in self.children:
            results.extend(child.find_all_by_class(class_name))
        return results

    def find_all_by_tag(self, tag_name):
        results = []
        if self.tag == tag_name.lower():
            results.append(self)
        for child in self.children:
            results.extend(child.find_all_by_tag(tag_name))
        return results

    def find_all(self, predicate):
        results = []
        if predicate(self):
            results.append(self)
        for child in self.children:
            results.extend(child.find_all(predicate))
        return results


class SimpleDOMParser(HTMLParser):
    """HTML Parser constructing a DOM tree of DOMElements."""
    def __init__(self):
        super().__init__()
        self.root = DOMElement("root")
        self.current = self.root
        self.stack = [self.root]
        self.void_tags = {
            "area", "base", "br", "col", "embed", "hr", "img",
            "input", "link", "meta", "param", "source", "track", "wbr"
        }

    def handle_starttag(self, tag, attrs):
        elem = DOMElement(tag, attrs)
        elem.parent = self.current
        self.current.children.append(elem)
        if tag.lower() not in self.void_tags:
            self.current = elem
            self.stack.append(elem)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag_lower:
                self.stack = self.stack[:idx]
                self.current = self.stack[-1]
                break

    def handle_data(self, data):
        clean = data.strip()
        if clean and self.current:
            if self.current.text_content:
                self.current.text_content += " " + clean
            else:
                self.current.text_content = clean


def parse_html_to_dom(html_content):
    """Parses raw HTML string into a queryable DOMElement tree."""
    parser = SimpleDOMParser()
    parser.feed(html_content)
    return parser.root


class CSSRule:
    """Represents a CSS rule with multiple selectors and declarations body."""
    def __init__(self, selectors, declarations):
        self.selectors = [s.strip() for s in selectors]
        self.declarations = declarations.strip()

    def matches_selector(self, target_selector):
        target = target_selector.strip()
        for sel in self.selectors:
            if sel == target or sel.endswith(" " + target) or sel.endswith("." + target) or ("," in sel and target in sel):
                return True
            # Also support pseudo-classes and compound matches
            if sel.startswith(target + ":") or sel.startswith(target + " "):
                return True
        return False

    def get_property_value(self, prop_name):
        pattern = rf"(?:^|;)\s*{re.escape(prop_name)}\s*:\s*([^;]+)"
        match = re.search(pattern, self.declarations, re.IGNORECASE)
        return match.group(1).strip() if match else None


class CSSAnalyzer:
    """Analyzes CSS content for rules, properties, and media queries."""
    def __init__(self, css_text):
        self.css_text = css_text
        self.clean_css = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
        self.rules = self._parse_rules(self.clean_css)

    def _parse_rules(self, text):
        rules = []
        for m in re.finditer(r"([^{}]+)\{([^{}]+)\}", text):
            sel_part = m.group(1).strip()
            body = m.group(2).strip()
            if sel_part.startswith("@"):
                continue
            selectors = [s.strip() for s in sel_part.split(",")]
            rules.append(CSSRule(selectors, body))
        return rules

    def has_selector(self, selector):
        target = selector.strip()
        for r in self.rules:
            for s in r.selectors:
                if target == s or target in s:
                    return True
        return False

    def get_rules_for_selector(self, selector):
        """Returns list of declarations bodies for any rule matching selector."""
        target = selector.strip()
        matching = []
        for r in self.rules:
            for s in r.selectors:
                if target == s or target in s or s.startswith(target + ":") or s.startswith(target + " "):
                    matching.append(r.declarations)
                    break
        return matching

    def selector_has_property(self, selector, prop_name, expected_val_substring=None):
        rules = self.get_rules_for_selector(selector)
        for rule in rules:
            prop_pattern = rf"(?:^|;)\s*{re.escape(prop_name)}\s*:\s*([^;]+)"
            match = re.search(prop_pattern, rule, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if expected_val_substring is None:
                    return True
                if expected_val_substring.lower() in val.lower():
                    return True
        return False

    def get_media_queries(self, max_width_px=None):
        """Extracts CSS contained in media queries."""
        pattern = r"@media\s*\(([^)]+)\)\s*\{((?:[^{}]+|\{[^{}]*\})+)\}"
        matches = re.findall(pattern, self.clean_css)
        results = []
        for cond, body in matches:
            if max_width_px is not None:
                if f"{max_width_px}px" in cond:
                    results.append((cond.strip(), body.strip()))
            else:
                results.append((cond.strip(), body.strip()))
        return results


def extract_i18n_dictionary(i18n_js_content):
    """
    Extracts the bilingual dictionary from public/js/i18n.js.
    Returns dict with 'es' and 'en' key mappings.
    """
    dict_match = re.search(r"const\s+I18N_DICTIONARY\s*=\s*\{([\s\S]+?)\};\s*(?:window\.)?", i18n_js_content)
    if not dict_match:
        dict_match = re.search(r"I18N_DICTIONARY\s*=\s*\{([\s\S]+?)\};", i18n_js_content)
    
    if not dict_match:
        raise ValueError("Could not locate I18N_DICTIONARY in i18n.js")

    body = dict_match.group(1)
    
    es_match = re.search(r"es\s*:\s*\{([\s\S]+?)\}\s*,\s*en\s*:\s*\{", body)
    en_match = re.search(r"en\s*:\s*\{([\s\S]+?)\}\s*$", body)
    
    def parse_kv_block(block_text):
        pairs = {}
        pattern = r'["\']([a-zA-Z0-9_\.]+)["\']\s*:\s*["\'](.*?)["\']\s*(?:,|$)'
        for m in re.finditer(pattern, block_text):
            k, v = m.group(1), m.group(2)
            pairs[k] = v
        return pairs

    es_dict = parse_kv_block(es_match.group(1)) if es_match else {}
    en_dict = parse_kv_block(en_match.group(1)) if en_match else {}

    return {"es": es_dict, "en": en_dict}
