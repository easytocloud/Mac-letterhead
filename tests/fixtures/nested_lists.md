# Nested Lists Test

This document tests nested list rendering functionality.

## Two-Level Nested Lists

### Unordered Nested Lists

- First level item 1
  - Second level item 1
  - Second level item 2
- First level item 2
  - Second level item 3
  - Second level item 4
    - Third level should not appear in 2-level test
- First level item 3

### Ordered Nested Lists

1. First level item 1
   1. Second level item 1
   2. Second level item 2
2. First level item 2
   1. Second level item 3
   2. Second level item 4
3. First level item 3

## Three-Plus Level Nesting

### Deep Unordered Nesting

- Level 1 item 1
  - Level 2 item 1
    - Level 3 item 1
      - Level 4 item 1
        - Level 5 item 1
        - Level 5 item 2
      - Level 4 item 2
    - Level 3 item 2
  - Level 2 item 2
- Level 1 item 2

### Deep Ordered Nesting

1. Level 1 item 1
   1. Level 2 item 1
      1. Level 3 item 1
         1. Level 4 item 1
            1. Level 5 item 1
            2. Level 5 item 2
         2. Level 4 item 2
      2. Level 3 item 2
   2. Level 2 item 2
2. Level 1 item 2

## Mixed Ordered/Unordered Nesting

### Ordered with Unordered Nested

1. Ordered item 1
   - Unordered sub-item 1
   - Unordered sub-item 2
     - Deeper unordered item
     - Another deeper item
2. Ordered item 2
   - Unordered sub-item 3
   - Unordered sub-item 4

### Unordered with Ordered Nested

- Unordered item 1
  1. Ordered sub-item 1
  2. Ordered sub-item 2
     1. Deeper ordered item
     2. Another deeper item
- Unordered item 2
  1. Ordered sub-item 3
  2. Ordered sub-item 4

## Complex Content Within Nested Items

- Level 1 with **bold formatting**
  - Level 2 with *italic formatting*
    - Level 3 with `code formatting`
      - Level 4 with [link](https://example.com)
        - Level 5 with all: **bold**, *italic*, `code`, [link](https://example.com)

1. Numbered item with table:
   
   | Column 1 | Column 2 |
   |----------|----------|
   | Data 1   | Data 2   |
   
   1. Sub-item after table
   2. Another sub-item

## Nested Lists with Different Starting Numbers

3. This list starts at 3
   5. This nested list starts at 5
   6. Next item should be 6
   7. Next item should be 7
4. Back to main list, should be 4
   1. This nested list restarts at 1
   2. Should be 2
5. Main list continues at 5