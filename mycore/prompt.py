class AuthorExtractionPrompt:
    @staticmethod
    def build() -> str:
        return """
Analyze this image of a research paper's first page.
Extract the author list and determine their specific roles based on these RULES:

1. **First Author**: The first name listed is ALWAYS the "First Author", UNLESS a symbol indicates equal contribution.
2. **Co-First Authors**: If a symbol (like † or ‡) notes "These authors contributed equally", then label ALL marked authors as "Co-First Author".
3. **Corresponding Author**: Look for an asterisk (*) or an email address in the footnotes. This person is "Corresponding Author" (they can also be First or Co-Author).
4. **Co-Author**: Everyone else is a "Co-Author".

Return ONLY a valid JSON object:
{
  "authors": [
    {
      "name": "Name",
      "role": "First Author / Co-First Author / Co-Author",
      "is_corresponding": true/false,
      "affiliation": "Affiliation",
      "email": "Email (only if available)"
    }
  ]
}
""".strip()
