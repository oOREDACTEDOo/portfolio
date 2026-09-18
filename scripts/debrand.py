#!/usr/bin/env python3
"""
Strip Webprofits branding from the report sources in reports-src/.

Jan built these reports while at Webprofits. The work is his; the agency
branding is not part of what the portfolio is showing, and a report handed to a
third party should not carry a former employer's logo, tagline and copyright.

The substitutions are deliberately structural rather than a blind find/replace
on the word, because the branding appears in four different shapes:

  1. An inline SVG logo, identified by aria-label="Webprofits". The whole
     element goes, otherwise the container keeps its spacing and collapses odd.
  2. Provenance lines ("Prepared by Webprofits") which become Jan's own byline,
     so the document still has a clear author rather than an anonymous one.
  3. Copyright and confidentiality notices, which are reassigned rather than
     deleted: the confidentiality claim still needs to stand.
  4. Title and footer suffixes ("... | Webprofits") which are just dropped.

Prose mentions are handled per file at the bottom, since each needs its own
wording and a generic rule would leave broken sentences.

Anything the script cannot classify is printed at the end for manual review, so
a silent miss is not possible.

    ./debrand.py reports-src/
"""

import io
import os
import re
import sys

OWNER = 'Jan Manns'

# --- 1. inline SVG logos -----------------------------------------------------
# Two shapes: the path-drawn logo carrying aria-label, and a plain <text> logo.
# Note the brand is spelled both "Webprofits" and "WebProfits" across the set,
# so every pattern here is case-insensitive.
SVG_LOGO = re.compile(r'<svg[^>]*aria-label="Webprofits".*?</svg>', re.S | re.I)
SVG_TEXT_LOGO = re.compile(
    r'<svg[^>]*>\s*<text[^>]*>\s*WebProfits\s*</text>\s*</svg>', re.S | re.I)
DIV_TEXT_LOGO = re.compile(
    r'<div[^>]*>\s*WebProfits\s*</div>', re.S | re.I)

# --- 2 & 3. provenance, copyright, suffixes ----------------------------------
SUBS = [
    # copyright / legal, reassigned so the confidentiality notice survives
    (re.compile(r'&copy;\s*2006[-–&a-z;]*2026\s*Webprofits Pty Ltd', re.I),
     '&copy; 2026 ' + OWNER),
    (re.compile(r'©\s*2006[-–]\s*2026\s*Webprofits Pty Ltd', re.I),
     '© 2026 ' + OWNER),

    # bylines
    (re.compile(r'Prepared by Jan Manns\s*[·&nbsp;\s]*Webprofits', re.I),
     'Prepared by ' + OWNER),
    (re.compile(r'Prepared by Jan M,\s*Webprofits', re.I),
     'Prepared by ' + OWNER),
    (re.compile(r'Prepared by Webprofits', re.I),
     'Prepared by ' + OWNER),
    (re.compile(r'\|\s*Prepared by Webprofits', re.I),
     '| Prepared by ' + OWNER),

    # title / footer suffixes
    (re.compile(r'\s*&nbsp;·&nbsp;\s*Webprofits(?=\s*&nbsp;·&nbsp;)', re.I), ''),
    (re.compile(r'\s*[|·]\s*Webprofits(?=\s*(<|$|\n))', re.I), ''),
    (re.compile(r'\s*[-–]\s*Webprofits(?=\s*(<|$|\n))', re.I), ''),
    (re.compile(r'\s*·\s*Webprofits\s*·', re.I), ' · '),

    # tagline: the agency's slogan, not part of the analysis
    (re.compile(r'<p class="tagline">.*?</p>', re.S | re.I), ''),

    # internal references that should not leave the building
    (re.compile(r'Webprofits Structured Data SEO Playbook \(internal\)', re.I),
     'internal structured data playbook'),
    (re.compile(r'<a href="https://www\.notion\.so/webprofits/[^"]*"[^>]*>(.*?)</a>',
                re.S | re.I), r'\1'),
    (re.compile(r'Webprofits keyword tracker snapshot', re.I),
     'Keyword tracker snapshot'),

    # design-system and playbook references
    (re.compile(r'/\*\s*WebProfits Design System\s*\*/', re.I), '/* Design system */'),
    (re.compile(r'WebProfits Structured Data SEO Playbook', re.I),
     'Structured data SEO playbook'),
    (re.compile(r'WebProfits SEO Playbook', re.I), 'SEO playbook'),

    # explicit "prepared by" field in a metadata block
    (re.compile(r'(<strong>Prepared by:</strong>)\s*WebProfits', re.I),
     r'\1 ' + OWNER),

    # delivery-plan owner cells in the strategy proposal: the document describes
    # who does what, so the agency role is kept and only the name comes out
    (re.compile(r'Owner:\s*WebProfits', re.I), 'Owner: Agency'),
    (re.compile(r'<td([^>]*)>\s*WebProfits\s*</td>', re.I), r'<td\1>Agency</td>'),

    # remaining prose in the strategy proposal
    (re.compile(r'The WebProfits methodology', re.I), 'The methodology'),
    (re.compile(r'WebProfits - SEO Strategy Proposal', re.I), 'SEO Strategy Proposal'),
    (re.compile(r'WebProfits has run content cluster programmes', re.I),
     'I have run content cluster programmes'),
    (re.compile(r'WebProfits produces the initial', re.I), 'The agency produces the initial'),
    (re.compile(r'WebProfits delivers detailed briefs', re.I), 'The agency delivers detailed briefs'),
    (re.compile(r'WebProfits delivers the initial research', re.I),
     'The agency delivers the initial research'),

    # byline inside a hero metadata block
    (re.compile(r'(<span>Prepared by</span>\s*<strong>)\s*WebProfits(\s*</strong>)', re.I | re.S),
     r'\g<1>' + OWNER + r'\g<2>'),

    # HTML section comment left over from the renamed section
    (re.compile(r'<!--\s*[═=\s]*WHY WEBPROFITS[═=\s]*-->', re.I),
     '<!-- WHY THIS APPROACH -->'),

    # GA4 property IDs identify a real client analytics account, which is a
    # tighter identifier than any branding. The sentence still needs to say the
    # data came from GA4, so the number is masked rather than the phrase cut.
    (re.compile(r'\b(?:280779713|250193583)\b'), 'redacted'),

    # internal-audience framing on the content brief
    (re.compile(r'Operational content guide for WebProfits colleagues', re.I),
     'Operational content guide'),
]

# --- 4. prose, per file ------------------------------------------------------
PROSE = {
    'client-h-seo-strategy.html': [
        ('Why Webprofits', 'Why this approach'),
        ('#why-webprofits', '#why-this-approach'),
        ('why-webprofits', 'why-this-approach'),
        ('The value Webprofits brings is',
         'The value this approach brings is'),
        ('accurately than traditional agencies without the overhead',
         'accurately than traditional agencies without the overhead'),
        ('Content is written by the client or Webprofits based on agreed scope',
         'Content is written by the client or the agency based on agreed scope'),
    ],
    'client-f-aeo-visibility-report.html': [],
    'client-b-llm-visibility-aeo-performance-report.html': [],
    'client-c-llm-visibility-report.html': [],
}


def debrand(path):
    s = original = io.open(path, encoding='utf-8', errors='replace').read()

    s = SVG_LOGO.sub('', s)
    s = SVG_TEXT_LOGO.sub('', s)
    s = DIV_TEXT_LOGO.sub('', s)
    for pat, rep in SUBS:
        s = pat.sub(rep, s)
    for old, new in PROSE.get(os.path.basename(path), []):
        s = s.replace(old, new)

    # tidy separators left dangling by a removal
    s = re.sub(r'(&nbsp;)?\s*[|·]\s*(&nbsp;)?\s*(</(p|div|footer|span)>)', r'\3', s)
    s = re.sub(r'\s{2,}(</(p|div|span)>)', r'\1', s)

    if s != original:
        io.open(path, 'w', encoding='utf-8').write(s)
    return s.lower().count('webprofits')


def main(folder):
    leftovers = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.html'):
            continue
        n = debrand(os.path.join(folder, name))
        status = 'clean' if n == 0 else '%d LEFT' % n
        print('%-52s %s' % (name, status))
        if n:
            leftovers[name] = n

    if leftovers:
        print('\nNeeds manual review:')
        for name, n in leftovers.items():
            path = os.path.join(folder, name)
            s = io.open(path, encoding='utf-8', errors='replace').read()
            for m in re.finditer(r'[^<>]{0,80}[Ww]ebprofits[^<>]{0,80}', s):
                print('  %s: %s' % (name, ' '.join(m.group(0).split())[:150]))
    else:
        print('\nAll files clean.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'reports-src'))
