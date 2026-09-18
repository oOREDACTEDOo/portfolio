import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# New keyword lists (copy from the edited file)
JOSETTE_YES_KEYWORDS = [
    "content brief", "write brief", "draft brief", "create brief",
    "keyword research", "keyword list", "keyword mapping",
    "keyword tracking", "rank tracker", "refine keywords",
    "faq", "faqs", "schema", "structured data",
    "competitor research", "competitor analysis",
    "data pull", "pull data", "export data", "fetch data",
    "reporting", "monthly report", "link report",
    "content creation", "draft content", "write content",
    "cluster page", "blog post", "blog content", "blog update",
    "earned media", "grant outreach",
    "seed question", "aeo question",
    "internal links", "internal link",
    "link building", "outreach target",
    "content schedule",
    "publish", "legacy blog",
    "fetch request",
]
JOSETTE_PARTIAL_KEYWORDS = [
    "content refresh", "content update", "update content",
    "audit", "page audit", "site audit",
    "brief", "create", "draft", "prepare",
    "review", "compile", "research",
    "landing page", "city page", "location page",
    "whitepaper", "repurpos",
    "optimis", "optimiz",
    "copy update", "product relaunch", "npd",
    "pillar page", "pillar and copy",
    "content process", "content framework",
    "monitoring report", "seo monitoring",
    "gds dashboard", "seo page",
    "collection page",
]
JOSETTE_NO_KEYWORDS = [
    "strategy", "strategic", "recommend", "advise", "prioriti",
    "client", "send to client", "present to client", "meeting",
    "decision", "approve", "sign off", "sign-off",
    "cro review", "budget", "scope",
    "email cam", "email darren", "email michelle", "email kathy", "email alex",
    "send jen", "send fathom", "send michelle",
    "follow up with", "contact", "reach out",
    "qsp", "quarterly strategic",
    "validate", "verify accuracy", "verify ga",
    "escalat", "blocker",
    "set up clarity", "clarity access", "microsoft clarity",
    "consent tracking", "discrepancy",
    "book-a-call", "downtime",
    "incorporate insight", "source quote", "source diverse",
    "site checker",
    "leads decline", "priority shift",
    "leave preparation", "leave prep",
    "lowercase brand", "fathom recording",
    "wip task",
]

def classify_josette(task_name, source=""):
    t = task_name.lower()
    src = source.lower()
    for kw in JOSETTE_YES_KEYWORDS:
        if kw in t:
            return ("YES", kw)
    for kw in JOSETTE_NO_KEYWORDS:
        if kw in t:
            return ("NO", kw)
    for kw in JOSETTE_PARTIAL_KEYWORDS:
        if kw in t:
            return ("PARTIAL", kw)
    if "slack" in src:
        return ("NO", "source=slack")
    if "meeting" in src or "fathom" in src:
        return ("NO", "source=meeting/fathom")
    return ("?", "no match")

# The 33 tasks that were "?"
tasks = [
    ("Client K", "Verify GA IP exclusions + confirm 2nd GA4 install", "Notion"),
    ("Client K", "Send Jen keyword bucket tool link", "Notion"),
    ("Client K", "Send Fathom access to Michelle/Jen", "Notion"),
    ("Client K", "Site Checker tool", "Notion"),
    ("Client K", "Set up Microsoft Clarity on US subdomain", "Notion"),
    ("Client K", "Update SEMrush keyword tracking for retail cluster", "Notion"),
    ("Client K", "Duplicate US rank tracker + refine keywords", "Notion"),
    ("Client K", "Start monthly US SEO monitoring report", "Notion"),
    ("Client K", "Add monthly detailed SEO page to GDS dashboard", "Notion"),
    ("Client K", "Add internal links/CTAs to high-traffic pages", "Notion"),
    ("Client K", "Incorporate executive insights into content", "Notion"),
    ("Client K", "Source diverse quotes for content", "Notion"),
    ("Client K", "Consent tracking discrepancy", "Notion"),
    ("Client K", "Clarity access", "Notion"),
    ("Client K", "Book-a-call downtime", "Notion"),
    ("Client K", "Publish ~70 legacy blogs in batches", "Notion"),
    ("Client K", "Initial Pillar Page Design (Retail)", "Notion"),
    ("Client C", "Link building campaign - confirm Feb outreach targets", "QSP"),
    ("Client C", "Collagen Collection Pages/Copy Update", "Notion"),
    ("Client C", "GUT PRIMER BLOG UPDATE", "Notion"),
    ("Client C", "NPDs Product Relaunches Feb 2026", "Notion"),
    ("Client C", "Cross-channel content process - top 50 search terms", "QSP"),
    ("Client C", "NPD content framework - adapt n8n workflow", "QSP"),
    ("Client A", "Content Schedule Sept-Dec", "Notion"),
    ("Client A", "Client A Storage Options Pillar and Copy", "Notion"),
    ("Client A", "Client A WIP tasks", "Notion"),
    ("Client A", "Leads decline", "Notion"),
    ("Client A", "Storage Options Pillar Page (designs)", "Notion"),
    ("Client O", "GSC fetch request", "Notion"),
    ("Client O", "Jess leave preparation", "Notion"),
    ("Client E", "Lowercase brand name in organic results", "Notion"),
    ("Client E", "Fathom recording flag", "Notion"),
    ("Client D", "ETF priority shift", "Notion"),
]

print(f"Testing {len(tasks)} previously-unclassified tasks:\n")
counts = {"YES": 0, "PARTIAL": 0, "NO": 0, "?": 0}
for client, task, source in tasks:
    result, matched_kw = classify_josette(task, source)
    counts[result] += 1
    flag = " << STILL UNCLASSIFIED" if result == "?" else ""
    print(f"  {result:7s} | {matched_kw:25s} | [{client}] {task}{flag}")

print(f"\nSummary: YES={counts['YES']}, PARTIAL={counts['PARTIAL']}, NO={counts['NO']}, ?={counts['?']}")

# Also check for conflicts: any task where a YES keyword matches but a NO keyword SHOULD match
print("\n--- Conflict check: YES keywords that are substrings of NO-intended tasks ---")
no_intended = ["Send Jen keyword bucket tool link", "Send Fathom access to Michelle/Jen", 
               "Verify GA IP exclusions", "Leads decline", "Jess leave preparation"]
for task in no_intended:
    result, kw = classify_josette(task, "Notion")
    if result == "YES":
        print(f"  CONFLICT: '{task}' classified YES via '{kw}' but should be NO")
    else:
        print(f"  OK: '{task}' correctly classified as {result} via '{kw}'")
