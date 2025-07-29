<!-- 
CSS Test Document for mac-letterhead WeasyPrint PDF Generation

This document intentionally violates some markdown-lint rules for testing purposes:
- MD033: Inline HTML elements (needed for HTML-specific styling tests)
- MD025: Multiple H1 headings (needed for heading hierarchy tests)
- MD040: Code block without language (testing generic code blocks)
- MD028: Blank lines in blockquotes (testing blockquote formatting)
- MD035: Mixed horizontal rule styles (testing different HR styles)
- MD036: Emphasis as heading (testing text styling)
- MD026: Trailing punctuation in headings (testing edge cases)

Other violations are fixed for cleaner output.
-->

# Complete CSS Test Document

This document tests all CSS styles defined in beautified.css for WeasyPrint PDF generation.

## Typography and Text Formatting

This is a regular paragraph with **bold text**, *italic text*, and ***bold italic text***. We can also use <u>underlined text</u>, ~~strikethrough text~~, and <small>small text</small>.

### Links and References

Here are different types of links:

- [Internal link](#headings-test)
- [External link](https://example.com)
- Raw URL: <https://example.com>

## Headings Test

<!-- MD025: Multiple H1 headings intentionally used for testing hierarchy -->

# Heading Level 1

## Heading Level 2

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

This paragraph follows directly after headings to test spacing.

## Lists

### Unordered Lists

- First level bullet point
- Another first level item
  - Second level bullet point
  - Another second level item
    - Third level bullet point
    - Another third level item
- Back to first level

### Ordered Lists

1. First ordered item
2. Second ordered item
   1. Nested ordered item
   2. Another nested item
      1. Deep nested item
      2. Another deep item
3. Back to main list

### Mixed Lists

1. Ordered item one
   - Unordered sub-item
   - Another unordered sub-item
2. Ordered item two
   1. Ordered sub-item
   2. Another ordered sub-item
      - Mixed nesting
      - Works well

## Code Examples

### Inline Code

Use the `print()` function in Python or `console.log()` in JavaScript.

### Code Blocks

```python
# Python code with syntax highlighting
def hello_world(name):
    """A simple function with a docstring."""
    message = f"Hello, {name}!"
    print(message)
    return message

# Example usage
result = hello_world("WeasyPrint")
```

```javascript
// JavaScript example
class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(num) {
        this.result += num;
        return this;
    }
    
    multiply(num) {
        this.result *= num;
        return this;
    }
}

const calc = new Calculator();
calc.add(5).multiply(3);
console.log(calc.result); // Output: 15
```

```bash
# Shell commands
$ echo "Testing code blocks"
$ ls -la /home/user/
$ grep -r "pattern" ./src/
```

### Code Block Without Language

<!-- MD040: Code block without language intentionally used for testing -->

```
This is a code block without syntax highlighting.
It should still be formatted as monospace text.
    With preserved indentation.
```

## Tables

### Simple Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Cell 1-1 | Cell 1-2 | Cell 1-3 |
| Cell 2-1 | Cell 2-2 | Cell 2-3 |
| Cell 3-1 | Cell 3-2 | Cell 3-3 |
| Cell 4-1 | Cell 4-2 | Cell 4-3 |

### Complex Table with Alignment

| Left Aligned | Center Aligned | Right Aligned | Default |
|:-------------|:--------------:|--------------:|---------|
| Left text    | Center text    | Right text    | Default |
| Lorem ipsum  | dolor sit      | amet          | text    |
| Another row  | With data      | Aligned       | properly|
| Final row    | Of the table   | Here          | done    |

## Blockquotes

> This is a simple blockquote. It should have special formatting with a left border and background color.

<!-- MD028: Blank lines in blockquotes intentionally used for testing -->

> Blockquotes can contain multiple paragraphs.
>
> Like this second paragraph within the same blockquote.

> Blockquotes can also contain other elements:
>
> - Lists work here
> - Another list item
>
> > And even nested blockquotes
> > work as expected.

## Horizontal Rules

Here's a horizontal rule:

---

<!-- MD035: Mixed HR styles intentionally used for testing -->

And another one:

***

## Images

![Alt text for image](image.png)

## Definition Lists (if supported)

<!-- MD033: HTML elements intentionally used for testing HTML support -->

<dl>
  <dt>Term 1</dt>
  <dd>Definition for term 1</dd>
  
  <dt>Term 2</dt>
  <dd>Definition for term 2</dd>
  <dd>Terms can have multiple definitions</dd>
  
  <dt>Term 3</dt>
  <dd>Another definition</dd>
</dl>

## Abbreviations (if supported)

<!-- MD033: HTML abbr elements intentionally used for testing -->

The <abbr title="World Wide Web Consortium">W3C</abbr> and <abbr title="Hypertext Markup Language">HTML</abbr> are important for web standards.

## Footnotes (if supported)

This text has a footnote[^1] and another one[^2].

[^1]: This is the first footnote.
[^2]: This is the second footnote with more text.

## Custom Classes (if markdown processor supports attributes)

{.text-center}
This paragraph should be center-aligned if attributes are supported.

{.text-right}
This paragraph should be right-aligned.

{.text-small}
This text should be smaller than normal.

{.text-large}
This text should be larger than normal.

{.highlight}
This text should be highlighted with a yellow background.

{.note}
**Note:** This is an informational note with special styling.

{.warning}
**Warning:** This is a warning message with appropriate styling.

{.error}
**Error:** This is an error message with red styling.

{.success}
**Success:** This is a success message with green styling.

## Edge Cases and Stress Tests

### Very Long Word

Thisissuperlongwordwithoutanyspacestotestwordbreakingbehaviorinweasyprint.

### Unicode and Special Characters

- Em dash — en dash – hyphen -
- Quotes: "double" and 'single'
- Smart quotes: "curly" and 'fancy'
- Symbols: © ® ™ § ¶ † ‡
- Math: ± × ÷ ≤ ≥ ≠ ≈ ∞ ∑ √ ∫
- Arrows: ← → ↑ ↓ ↔ ⇐ ⇒
- Emoji: 😀 🎉 ❤️ ✓ ✗

### Deep Nesting Test

> Level 1 quote
> > Level 2 quote
> > > Level 3 quote
> > > > Level 4 quote
> > > > > Level 5 quote

### Empty Elements

Empty paragraph below:

Empty list items:

- <!-- empty item for testing -->
- Item with text
- <!-- another empty item -->

### Page Break Tests

This content is before a potential page break. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

<!-- MD033: HTML div element intentionally used for page break testing -->

<div style="page-break-after: always;"></div>

This content should appear on a new page if page breaks are respected.

## Final Test Section

This is the final section to ensure the document renders completely. All styles should have been tested above. The page number at the bottom should be visible and styled according to the CSS.

---

<!-- MD036: Emphasis as heading intentionally used for testing -->

*End of CSS test document*
