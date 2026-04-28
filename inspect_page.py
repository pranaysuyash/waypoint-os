#!/usr/bin/env python3
"""
Inspect the actual page structure to understand the DOM.
"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Navigating to http://localhost:3000/workspace/trip-demo...")
    page.goto("http://localhost:3000/workspace/trip-demo", wait_until="networkidle")
    
    # Wait for JavaScript to execute
    page.wait_for_timeout(3000)
    
    # Get page content
    content = page.content()
    
    # Check page title
    title = page.title()
    print(f"Page title: {title}")
    
    # Check for specific elements
    buttons = page.locator("button").all()
    print(f"\nTotal buttons: {len(buttons)}")
    for i, btn in enumerate(buttons[:10]):
        try:
            text = btn.text_content()
            print(f"  {i+1}. {text}")
        except:
            print(f"  {i+1}. [unable to read text]")
    
    # Check for divs with specific text
    print("\nSearching for 'Capture Call' text anywhere on page...")
    try:
        elements = page.locator("text=Capture Call")
        count = elements.count()
        print(f"  Found 'Capture Call' in {count} element(s)")
    except:
        print("  'Capture Call' text not found")
    
    # Look for IntakePanel
    print("\nSearching for IntakePanel-like elements...")
    try:
        intake_elements = page.locator("[class*='Intake']").all()
        print(f"  Found {len(intake_elements)} Intake-related elements")
    except:
        pass
    
    # Check for any action buttons
    print("\nLooking for action buttons...")
    try:
        action_buttons = page.locator("[class*='action'], [class*='Action']").all()
        print(f"  Found {len(action_buttons)} action-related elements")
    except:
        pass
    
    # Save the content to a file for inspection
    with open("page_content.html", "w") as f:
        f.write(content)
    print("\nPage content saved to page_content.html")
    
    # Take a screenshot
    page.screenshot(path="page_inspect.png", full_page=True)
    print("Screenshot saved to page_inspect.png")
    
    browser.close()
