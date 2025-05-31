#!/usr/bin/env python3
"""
Quick configuration tool for rate limiting settings.

This script provides an easy way to view and modify rate limiting
configurations for the scraper.
"""

import sys
import json
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.rate_limits.domain_config import (
    DOMAIN_RATE_LIMITS,
    get_domain_rate_limit,
    update_domain_rate_limit,
    apply_rate_limit_category
)


def list_domains():
    """List all configured domains."""
    print("\nConfigured Domains:")
    print("-" * 60)
    print(f"{'Domain':<30} {'Delay':<10} {'Concurrency':<12} {'Randomize'}")
    print("-" * 60)
    
    for domain in sorted(DOMAIN_RATE_LIMITS.keys()):
        config = DOMAIN_RATE_LIMITS[domain]
        print(
            f"{domain:<30} "
            f"{config.get('delay', 'N/A'):<10} "
            f"{config.get('concurrency', 'N/A'):<12} "
            f"{config.get('randomize_delay', False)}"
        )
    print()


def show_domain(domain: str):
    """Show configuration for a specific domain."""
    config = get_domain_rate_limit(domain)
    
    print(f"\nConfiguration for {domain}:")
    print("-" * 40)
    print(f"Delay: {config.get('delay', 'N/A')} seconds")
    print(f"Concurrency: {config.get('concurrency', 'N/A')} requests")
    print(f"Randomize Delay: {config.get('randomize_delay', False)}")
    print()


def update_domain(domain: str, delay: Optional[float] = None, 
                 concurrency: Optional[int] = None, 
                 randomize: Optional[bool] = None):
    """Update configuration for a domain."""
    current = get_domain_rate_limit(domain)
    
    # Update only provided values
    if delay is not None:
        current['delay'] = delay
    if concurrency is not None:
        current['concurrency'] = concurrency
    if randomize is not None:
        current['randomize_delay'] = randomize
    
    update_domain_rate_limit(domain, current)
    
    print(f"\nUpdated configuration for {domain}:")
    show_domain(domain)


def apply_category(domain: str, category: str):
    """Apply a predefined category to a domain."""
    try:
        apply_rate_limit_category(domain, category)
        print(f"\nApplied '{category}' category to {domain}")
        show_domain(domain)
    except ValueError as e:
        print(f"Error: {e}")


def export_config(filename: str):
    """Export current configuration to JSON file."""
    with open(filename, 'w') as f:
        json.dump(DOMAIN_RATE_LIMITS, f, indent=2)
    print(f"\nConfiguration exported to {filename}")


def import_config(filename: str):
    """Import configuration from JSON file."""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        
        # Update all domains
        for domain, settings in config.items():
            update_domain_rate_limit(domain, settings)
        
        print(f"\nConfiguration imported from {filename}")
        print(f"Updated {len(config)} domains")
    except Exception as e:
        print(f"Error importing configuration: {e}")


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Configure rate limiting for the scraper'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all configured domains')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show domain configuration')
    show_parser.add_argument('domain', help='Domain to show')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update domain configuration')
    update_parser.add_argument('domain', help='Domain to update')
    update_parser.add_argument('--delay', type=float, help='Delay in seconds')
    update_parser.add_argument('--concurrency', type=int, help='Max concurrent requests')
    update_parser.add_argument('--randomize', type=bool, help='Randomize delay (true/false)')
    
    # Category command
    category_parser = subparsers.add_parser('category', help='Apply category to domain')
    category_parser.add_argument('domain', help='Domain to configure')
    category_parser.add_argument(
        'category', 
        choices=['default', 'conservative', 'aggressive'],
        help='Category to apply'
    )
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('filename', help='Output filename')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import configuration')
    import_parser.add_argument('filename', help='Input filename')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_domains()
    elif args.command == 'show':
        show_domain(args.domain)
    elif args.command == 'update':
        update_domain(
            args.domain,
            delay=args.delay,
            concurrency=args.concurrency,
            randomize=args.randomize
        )
    elif args.command == 'category':
        apply_category(args.domain, args.category)
    elif args.command == 'export':
        export_config(args.filename)
    elif args.command == 'import':
        import_config(args.filename)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
