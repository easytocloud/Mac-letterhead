# Mixed Content Lists Test

This document tests lists with complex content types.

## Lists with Code Blocks

- Item before code block
- Item with code block:
  
  ```python
  def example_function():
      print("Hello from inside a list!")
      return True
  ```
  
- Item after code block

1. Numbered item before code
2. Numbered item with code block:
   
   ```javascript
   function listExample() {
       console.log("Code in numbered list");
       return { success: true };
   }
   ```
   
3. Numbered item after code

## Lists with Tables

- Bullet item with table:
  
  | Header 1 | Header 2 | Header 3 |
  |----------|----------|----------|
  | Row 1A   | Row 1B   | Row 1C   |
  | Row 2A   | Row 2B   | Row 2C   |
  
- Another bullet item after table

1. Numbered item with complex table:
   
   | Feature | WeasyPrint | ReportLab | Notes |
   |---------|:----------:|:---------:|-------|
   | Tables  | ✓          | ✓         | Both support |
   | CSS     | ✓          | ⚠️        | Limited in ReportLab |
   | Images  | ✓          | ✓         | Both support |
   
2. Item after complex table

## Lists with Images

- Item with image reference:
  
  ![Test Image](test-image.png)
  
- Item after image

1. Numbered item with image
   
   ![Another Image](another-image.png)
   
2. Item continuing after image

## Lists with Blockquotes

- Item with blockquote:
  
  > This is a blockquote within a list item.
  > It should be properly indented and formatted.
  
- Item after blockquote

1. Numbered item with nested blockquote:
   
   > First level quote
   > > Nested quote within list
   > > Still nested
   > Back to first level
   
2. Item after nested blockquote

## Lists with Nested Lists and Mixed Content

- Top level item
  
  This paragraph is part of the list item.
  
  - Nested list item
    
    ```bash
    # Code block in nested item
    echo "Complex nesting"
    ```
    
  - Another nested item with table:
    
    | Col 1 | Col 2 |
    |-------|-------|
    | A     | B     |
    
- Back to top level

1. Numbered top level
   
   Multiple paragraphs in this item.
   
   This is the second paragraph.
   
   1. Nested numbered item
      
      > Blockquote in nested numbered item
      
   2. Another nested item
      
      ![Image in nested item](nested-image.png)
      
2. Back to main numbered list

## Lists Immediately After Headers

### Header 3
- List immediately after header
- No blank line between header and list

#### Header 4
1. Numbered list after header
2. Also no blank line

##### Header 5
- Mixed list types
  1. Nested numbered in unordered
  2. Should work properly

## Lists at End of Document

- Final list item 1
- Final list item 2
  - Nested final item
  - Last nested item
- Very last item in document