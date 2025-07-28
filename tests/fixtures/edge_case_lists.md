# Edge Case Lists Test

This document tests unusual list rendering edge cases.

## Lists with Unusual Spacing

-    Extra spaces before content
-	Tab character before content
- Normal spacing
-No space after dash
- 

## Lists with Special Characters

- Item with em dash — character
- Item with en dash – character  
- Item with various quotes: "smart" 'quotes' «guillemets»
- Item with math symbols: ∑ ∫ √ ± × ÷ ≤ ≥ ≠
- Item with arrows: → ← ↑ ↓ ⇒ ⇐ ↔
- Item with currency: $ € £ ¥ ₹ ₽ ₿

## Lists with Unicode and Emoji

- Item with emoji: 😀 🎉 ❤️ 🚀 📄 ✅ ❌ ⚠️
- Item with symbols: ☀️ ⭐ 🌙 ⚡ 🔥 💧 🌈
- Item with flags: 🇺🇸 🇬🇧 🇫🇷 🇩🇪 🇯🇵 🇮🇳
- Item with accented characters: café naïve résumé piñata
- Item with non-Latin scripts: 中文 日本語 العربية हिंदी русский

## Lists with Very Long Words

- Supercalifragilisticexpialidocious
- Pneumonoultramicroscopicsilicovolcanoconiosispneumonoultramicroscopicsilicovolcanoconiosis
- Thisissuperlongwordwithoutanyspacesorbreakstotestwordwrappingbehavior
- Normal word after long words

## Lists with URLs and Email

- https://www.verylongdomainname.com/with/very/long/path/and/parameters?query=value&another=parameter
- Short URL: https://bit.ly/abc
- Email: verylongemailaddress@verylongdomainname.co.uk
- FTP: ftp://files.example.com/path/to/file.txt

## Malformed List Markers

* Mixed bullet types in same list
+ Plus sign bullet
* Back to asterisk
- Hyphen bullet
+ Plus again

1) Parenthesis instead of period
2. Normal period
3) Parenthesis again
4. Period again

## Lists with Inline HTML

- Item with <strong>HTML bold</strong> and <em>HTML italic</em>
- Item with <code>HTML code</code> tags
- Item with <a href="https://example.com">HTML link</a>
- Item with <span style="color: red;">styled span</span>
- Item with <br/> line break
- Item with <del>strikethrough</del> and <ins>underline</ins>

## Lists with Markdown Edge Cases

- Item with `code` and **bold** and *italic* all mixed
- Item with ***bold italic*** formatting
- Item with ~~strikethrough~~ text
- Item with [link with **bold** text](https://example.com)
- Item with ![image with *italic* alt text](test.png)

## Lists with Escape Characters

- Item with \*escaped asterisks\*
- Item with \[escaped brackets\]
- Item with \`escaped backticks\`
- Item with \\backslashes\\
- Item with \- escaped list marker

## Deeply Nested Empty Lists

- Level 1
  - Level 2
    - Level 3
      - Level 4
        - Level 5
          - 
        - 
      - 
    - 
  - 
- 

## Lists with Mixed Line Endings

- Item with Unix line ending
- Item with potential Windows line ending
- Item with Mac line ending

## Lists at Document Boundaries

First line is a list:
- Very first content
- Second item

Last content is also a list:
- Second to last item
- Very last content in document