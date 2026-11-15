"""Menu registry for extensible shell architecture."""

MENU_STRUCTURE = {
    "Web Analysis": [
        {"name": "Recon", "desc": "Analyze single page", "handler": "do_recon"},
        {"name": "Crawl", "desc": "Map links and forms", "handler": "do_crawl"},
        {"name": "Web Profiler", "desc": "WAF, Headers, Cookies", "handler": "do_profile"}
    ],
    "Network Tools": [
        {"name": "Nmap", "desc": "Port scanner", "handler": "do_nmap"},
        {"name": "WhatWeb", "desc": "Fingerprinting", "handler": "do_whatweb"}
    ],
    "Utilities": [
        {"name": "Target", "desc": "Set global target", "handler": "do_target"},
        {"name": "Scope", "desc": "Manage whitelist", "handler": "do_scope"},
        {"name": "Reports", "desc": "View reports", "handler": "do_reports"},
        {"name": "Sessions", "desc": "Manage cookie sessions", "handler": "do_sessions"},
        {"name": "Wordlists", "desc": "Manage wordlists", "handler": "do_wordlists"},
        {"name": "Cookies", "desc": "View stored cookies", "handler": "do_cookies"}
    ]
}
