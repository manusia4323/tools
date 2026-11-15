"""Registry of external tools with multi-method installation support."""

TOOL_REGISTRY = {
    "nmap": {
        "category": "network",
        "install": {
            "apt": "sudo apt install nmap",
            "pacman": "sudo pacman -S nmap",
            "dnf": "sudo dnf install nmap",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Network exploration and security auditing",
        "api_token_needed": False,
    },
    "whatweb": {
        "category": "web",
        "install": {
            "apt": "sudo apt install whatweb",
            "pacman": "sudo pacman -S whatweb",
            "dnf": "sudo dnf install whatweb",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Web scanner to identify what websites are running",
        "api_token_needed": False,
    },
    "rustscan": {
        "category": "network",
        "install": {
            "apt": None,  # Not available in apt
            "pacman": "sudo pacman -S rustscan",
            "dnf": None,
            "cargo": "cargo install rustscan",
        },
        "requires_aur": True,  # On Arch, available in AUR
        "requires_go": False,
        "desc": "Fast modern port scanner",
        "api_token_needed": False,
    },
    "arp-scan": {
        "category": "network",
        "install": {
            "apt": "sudo apt install arp-scan",
            "pacman": "sudo pacman -S arp-scan",
            "dnf": "sudo dnf install arp-scan",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "ARP scanning and fingerprinting tool",
        "api_token_needed": False,
    },
    "netdiscover": {
        "category": "network",
        "install": {
            "apt": "sudo apt install netdiscover",
            "pacman": "sudo pacman -S netdiscover",
            "dnf": "sudo dnf install netdiscover",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Active/passive ARP reconnaissance tool",
        "api_token_needed": False,
    },
    "nikto": {
        "category": "web",
        "install": {
            "apt": "sudo apt install nikto",
            "pacman": "sudo pacman -S nikto",
            "dnf": "sudo dnf install nikto",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Web server scanner",
        "api_token_needed": False,
    },
    "gobuster": {
        "category": "web",
        "install": {
            "apt": "sudo apt install gobuster",
            "pacman": "sudo pacman -S gobuster",
            "dnf": "sudo dnf install gobuster",
            "go": "go install github.com/OJ/gobuster/v3@latest",
        },
        "requires_aur": False,
        "requires_go": True,
        "desc": "Directory/file & DNS busting tool",
        "api_token_needed": False,
    },
    "ffuf": {
        "category": "web",
        "install": {
            "apt": None,  # Not in default repos
            "pacman": "sudo pacman -S ffuf",
            "dnf": None,
            "go": "go install github.com/ffuf/ffuf/v2@latest",
        },
        "requires_aur": True,  # On Arch via AUR
        "requires_go": True,
        "desc": "Fast web fuzzer",
        "api_token_needed": False,
    },
    "wpscan": {
        "category": "wordpress",
        "install": {
            "apt": "sudo apt install wpscan",
            "pacman": "sudo pacman -S wpscan",
            "dnf": "sudo dnf install wpscan",
            "gem": "gem install wpscan",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "WordPress Security Scanner",
        "api_token_needed": True,
    },
    "hydra": {
        "category": "cracker",
        "install": {
            "apt": "sudo apt install hydra",
            "pacman": "sudo pacman -S hydra",
            "dnf": "sudo dnf install hydra",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Network logon cracker",
        "api_token_needed": False,
    },
    "medusa": {
        "category": "cracker",
        "install": {
            "apt": "sudo apt install medusa",
            "pacman": "sudo pacman -S medusa",
            "dnf": "sudo dnf install medusa",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Parallel network login auditor",
        "api_token_needed": False,
    },
    "hashcat": {
        "category": "cracker",
        "install": {
            "apt": "sudo apt install hashcat",
            "pacman": "sudo pacman -S hashcat",
            "dnf": "sudo dnf install hashcat",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Advanced password recovery",
        "api_token_needed": False,
    },
    "john": {
        "category": "cracker",
        "install": {
            "apt": "sudo apt install john",
            "pacman": "sudo pacman -S john",
            "dnf": "sudo dnf install john",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "John the Ripper password cracker",
        "api_token_needed": False,
    },
    "nc": {
        "category": "listener",
        "install": {
            "apt": "sudo apt install netcat",
            "pacman": "sudo pacman -S openbsd-netcat",
            "dnf": "sudo dnf install nmap-ncat",
        },
        "binary_name": "nc",
        "requires_aur": False,
        "requires_go": False,
        "desc": "TCP/IP swiss army knife",
        "api_token_needed": False,
    },
    "socat": {
        "category": "listener",
        "install": {
            "apt": "sudo apt install socat",
            "pacman": "sudo pacman -S socat",
            "dnf": "sudo dnf install socat",
        },
        "requires_aur": False,
        "requires_go": False,
        "desc": "Multipurpose relay for data transfer",
        "api_token_needed": False,
    },
    "nth": {
        "category": "cracker",
        "install": {
            "pip": "pip install name-that-hash",
        },
        "binary_name": "nth",
        "requires_aur": False,
        "requires_go": False,
        "desc": "Hash identification tool",
        "api_token_needed": False,
    },
}

# Categories for menu organization
TOOL_CATEGORIES = {
    "network": "Network Scanning & Discovery",
    "web": "Web Application Analysis",
    "wordpress": "WordPress Security",
    "cracker": "Password & Credential Testing",
    "listener": "Network Listeners & Shells",
    "osint": "Open Source Intelligence",
}
