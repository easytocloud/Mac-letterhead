# GitHub Flavored Markdown Features Test

This document tests the GitHub Flavored Markdown features that are now supported.

## Strikethrough Text

~~This text is struck through~~

Regular text with ~~strikethrough~~ in the middle.

Multiple ~~strikethrough~~ sections ~~in one~~ paragraph.

## Task Lists

### Simple Task Lists

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task
- [ ] Another incomplete task

### Mixed Lists with Tasks

1. Regular numbered item
2. [x] Completed task in numbered list
3. [ ] Incomplete task in numbered list
4. Regular numbered item again

### Nested Task Lists

- [x] Top level completed task
  - [x] Nested completed task
  - [ ] Nested incomplete task
- [ ] Top level incomplete task
  - [x] Nested completed under incomplete parent
  - [ ] Nested incomplete task

## Tables (Already supported in standard markdown)

| Task | Status | Priority |
|------|--------|----------|
| ~~Implement strikethrough~~ | [x] Complete | High |
| Task lists | [x] Complete | High |
| Table support | [x] Complete | Medium |
| ~~Old feature~~ | [x] Deprecated | ~~Low~~ |

## Code Blocks with Language

```python
# This should work the same as before
def test_gfm():
    return "GitHub Flavored Markdown works!"
```

## Links and References

Regular [link](https://example.com) should work.

Autolinks should work: https://github.com/anthropics/claude

## Mixed Content

Here's a paragraph with **bold**, *italic*, ~~strikethrough~~, and `inline code`.

Task list after paragraph:
- [x] This should work
- [ ] This should also work

End of GFM features test.