# Malformed Lists Test

This document tests how the system handles malformed HTML from Markdown conversion.

## Incomplete List Tags

<ul>
<li>Item 1
<li>Item 2 without closing tag
<li>Item 3</li>
</ul>

<ol>
<li>Numbered item 1
<li>Numbered item 2 without closing tag
</ol>

## Mixed List Types

<ul>
<li>Unordered item 1</li>
<ol>
<li>Ordered item inside unordered list</li>
</ol>
<li>Back to unordered</li>
</ul>

## Nested Lists Without Proper Structure

<ul>
<li>Item 1
<ul>
<li>Nested item
</li>
</ul>
<li>Item 2
</ul>

## Lists with Invalid Attributes

<ul class="invalid-class" id="test-id" data-custom="value">
<li style="color: red; background: yellow;">Styled list item</li>
<li onclick="alert('click')">Item with JS (should be ignored)</li>
</ul>

## Lists with Self-Closing Tags

<ul/>
<li>Orphaned list item</li>

## Lists with Text Nodes in Wrong Places

<ul>
Text outside list items
<li>Proper list item</li>
More text outside
<li>Another proper item</li>
</ul>

## Lists with Deeply Nested Malformed Structure

<ul>
<li>Level 1
<ul>
<li>Level 2
<ul>
<li>Level 3
<ul>
<li>Level 4 - missing some closing tags
</ul>
</li>
</ul>
</ul>

## Lists with Unknown Tags

<ul>
<li>Normal item</li>
<unknown-tag>Unknown content</unknown-tag>
<li>Another normal item</li>
</ul>

## Lists with Comments and CDATA

<ul>
<!-- This is a comment -->
<li>Item 1</li>
<![CDATA[This is CDATA content]]>
<li>Item 2</li>
</ul>

## Lists with Mixed Content Models

<ul>
<li>
<div>Block element inside list item</div>
<span>Inline element</span>
<p>Paragraph inside list item</p>
</li>
</ul>

## Lists with Entities and Special Characters

<ul>
<li>&lt; &gt; &amp; &quot; &#39;</li>
<li>&#8364; &#8482; &#169;</li>
<li>Malformed entities: &invalid; &;</li>
</ul>

## Lists with Malformed Markdown

- Item with unclosed **bold
- Item with unclosed *italic  
- Item with unclosed `code
- Item with [unclosed link(https://example.com)
- Item with ![unclosed image(alt text)

## Lists with Conflicting Numbering

1. Item 1
5. Item with number 5 (should this be 2?)
2. Item with number 2 (should this be 3?)
10. Item with number 10

## Lists with Invalid Characters in Markdown

- Item with null character: 
- Item with control characters: 
- Item with zero-width spaces: ​invisible​content​

## Empty and Whitespace-Only Lists

<ul>
</ul>

<ol>
   
</ol>

<ul>
<li></li>
<li>   </li>
<li>	</li>
</ul>

## Lists with Script and Style Tags (Should be Filtered)

<ul>
<li>Normal item</li>
<script>alert('This should not execute');</script>
<li>Another normal item</li>
<style>body { background: red; }</style>
</ul>