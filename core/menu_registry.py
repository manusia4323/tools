"""Menu registry for extensible shell architecture."""

MENU_TREE = {
    "Web Analysis": {
        "desc": "Analyze websites (Recon, Crawl, Profiler)",
        "items": {
            "Recon": {"handler": "do_recon", "desc": "Single page analyze"},
            "Crawl": {"handler": "do_crawl", "desc": "Map links and forms"},
            "Web Profiler": {"handler": "do_profile", "desc": "WAF, Headers, Cookies"},
        },
    },
    "Network Tools": {
        "desc": "Scan and discover networks",
        "items": {
            "Port Scanners": {
                "desc": "Find open ports",
                "items": {
                    "Nmap": {"handler": "do_nmap", "desc": "Port scanner & service detection"},
                    "RustScan": {"handler": "do_rustscan", "desc": "Fast port scanner"},
                },
            },
            "Discovery": {
                "desc": "Find local hosts",
                "items": {
                    "Arp-Scan": {"handler": "do_arpscan", "desc": "Local network discovery"},
                    "Netdiscover": {"handler": "do_netdiscover", "desc": "Active/passive ARP recon"},
                },
            },
            "WhatWeb": {"handler": "do_whatweb", "desc": "Web fingerprinting"},
        },
    },
    "OSINT": {
        "desc": "Open-source intelligence tools",
        "items": {},
    },
    "Cracker": {
        "desc": "Password & credential testing",
        "items": {},
    },
    "Listener": {
        "desc": "Network listeners & shells",
        "items": {},
    },
    "Utilities": {
        "desc": "Target, scope, reports, and sessions",
        "items": {
            "Target": {"handler": "do_target", "desc": "Set global target"},
            "Scope": {"handler": "do_scope", "desc": "Manage whitelist"},
            "Reports": {"handler": "do_reports", "desc": "View reports"},
            "Sessions": {"handler": "do_sessions", "desc": "Manage cookie sessions"},
            "Wordlists": {"handler": "do_wordlists", "desc": "Manage wordlists"},
            "Cookies": {"handler": "do_cookies", "desc": "View stored cookies"},
        },
    },
}

# Backward compatibility alias
MENU_STRUCTURE = MENU_TREE
