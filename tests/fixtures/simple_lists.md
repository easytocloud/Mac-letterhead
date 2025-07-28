# Simple Lists Test

This document tests basic list rendering functionality.

## Simple Bulleted Lists

- First bullet point
- Second bullet point
- Third bullet point with **bold text**
- Fourth bullet point with *italic text*
- Fifth bullet point with `inline code`

## Simple Numbered Lists

1. First numbered item
2. Second numbered item
3. Third numbered item with **bold text**
4. Fourth numbered item with *italic text*
5. Fifth numbered item with `inline code`

## Lists with Long Text

- This is a very long bullet point that should wrap to multiple lines and test how the rendering handles text wrapping within list items. The indentation should be preserved properly.
- Another long item with even more text to ensure that word wrapping works correctly across different backends and that the bullet alignment is maintained throughout the wrapping.

1. This is a very long numbered item that should wrap to multiple lines and test how the rendering handles text wrapping within numbered list items. The numbering should align properly.
2. Another long numbered item with extensive text to verify that word wrapping works correctly and the number alignment is maintained across line breaks.

## Empty List Items

- 
- Item with content
- 
- Another item with content
- 

1. 
2. Item with content
3. 
4. Another item with content
5. 

## Mixed Content Within List Items

- Item with **bold**, *italic*, and `code` formatting
- Item with [a link](https://example.com) embedded
- Item with inline HTML <strong>elements</strong>
- Item with emoji: 🎉 ✓ ❌ 
- Item with special characters: © ® ™ § ¶