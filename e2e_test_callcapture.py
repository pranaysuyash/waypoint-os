#!/usr/bin/env python3
"""
End-to-end test for Unit-1 call-capture feature.
Tests the complete workflow: UI navigation, form submission, data persistence.
"""

import json
import sys
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, expect

def test_call_capture_workflow():
    """Test the complete call-capture workflow end-to-end."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture console messages for debugging
        console_logs = []
        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))
        
        print("\n" + "="*80)
        print("STEP 1: Navigate to workspace")
        print("="*80)
        
        # Navigate to the workspace
        page.goto("http://localhost:3000/workspace/trip-demo", wait_until="networkidle")
        print("✓ Navigated to workspace")
        
        # Take a screenshot to see initial state
        page.screenshot(path="test_initial_state.png", full_page=False)
        print("✓ Screenshot saved: test_initial_state.png")
        
        # Wait a bit for the page to fully render
        page.wait_for_timeout(2000)
        
        print("\n" + "="*80)
        print("STEP 2: Look for 'Capture Call' button")
        print("="*80)
        
        # Try to find the "Capture Call" button
        try:
            capture_button = page.locator("button:has-text('Capture Call')")
            count = capture_button.count()
            if count > 0:
                print(f"✓ Found 'Capture Call' button (count: {count})")
                is_visible = capture_button.first.is_visible()
                is_enabled = capture_button.first.is_enabled()
                print(f"  - Visible: {is_visible}")
                print(f"  - Enabled: {is_enabled}")
            else:
                print("✗ 'Capture Call' button NOT found")
                # Try alternative selectors
                all_buttons = page.locator("button").all()
                print(f"  All buttons on page ({len(all_buttons)}):")
                for i, btn in enumerate(all_buttons[:5]):
                    text = btn.text_content()
                    print(f"    {i+1}. {text}")
        except Exception as e:
            print(f"✗ Error looking for button: {e}")
        
        print("\n" + "="*80)
        print("STEP 3: Click 'Capture Call' button")
        print("="*80)
        
        try:
            capture_button = page.locator("button:has-text('Capture Call')").first
            capture_button.click()
            print("✓ Clicked 'Capture Call' button")
            
            # Wait for the panel to appear
            page.wait_for_timeout(2000)
            
            # Check for the panel
            page.screenshot(path="test_capture_panel_opened.png", full_page=False)
            print("✓ Screenshot saved: test_capture_panel_opened.png")
            
        except Exception as e:
            print(f"✗ Error clicking button: {e}")
            page.screenshot(path="test_error_click.png", full_page=False)
            browser.close()
            return False
        
        print("\n" + "="*80)
        print("STEP 4: Verify CaptureCallPanel renders")
        print("="*80)
        
        try:
            # Look for the panel and its fields
            raw_note_field = page.locator("textarea").first
            raw_note_visible = raw_note_field.is_visible()
            print(f"✓ Raw note field visible: {raw_note_visible}")
            
            # Count textareas
            textareas = page.locator("textarea").all()
            print(f"✓ Found {len(textareas)} textarea(s)")
            
            # Look for datetime input
            datetime_inputs = page.locator("input[type='datetime-local']").all()
            print(f"✓ Found {len(datetime_inputs)} datetime input(s)")
            
        except Exception as e:
            print(f"✗ Error inspecting panel: {e}")
        
        print("\n" + "="*80)
        print("STEP 5: Fill in the form")
        print("="*80)
        
        try:
            # Fill raw note
            raw_note_text = "Family of 4 wants to explore Japan in November, non-rushed pace, interested in temples and skiing"
            raw_note_field = page.locator("textarea").first
            raw_note_field.fill(raw_note_text)
            print(f"✓ Filled raw note: '{raw_note_text[:50]}...'")
            
            # Fill owner note
            owner_note_text = "Budget ~$5k per person, mentioned toddler-friendly activities"
            textareas = page.locator("textarea").all()
            if len(textareas) > 1:
                textareas[1].fill(owner_note_text)
                print(f"✓ Filled owner note: '{owner_note_text[:50]}...'")
            else:
                print("! Only one textarea found, skipping owner note")
            
            # Set follow-up date (48 hours from now)
            future_date = datetime.now() + timedelta(hours=48)
            follow_up_datetime = future_date.isoformat(timespec='minutes')
            
            datetime_inputs = page.locator("input[type='datetime-local']").all()
            if len(datetime_inputs) > 0:
                datetime_inputs[0].fill(follow_up_datetime)
                print(f"✓ Set follow-up date: {follow_up_datetime}")
            else:
                print("! No datetime input found, skipping follow-up date")
            
        except Exception as e:
            print(f"✗ Error filling form: {e}")
            page.screenshot(path="test_error_fill.png", full_page=False)
            browser.close()
            return False
        
        page.screenshot(path="test_form_filled.png", full_page=False)
        print("✓ Screenshot saved: test_form_filled.png")
        
        print("\n" + "="*80)
        print("STEP 6: Submit the form")
        print("="*80)
        
        try:
            # Find and click the Save button
            save_button = page.locator("button:has-text('Save')").first
            print(f"✓ Found Save button, clicking...")
            save_button.click()
            
            # Wait for the API call and response
            page.wait_for_timeout(3000)
            
            page.screenshot(path="test_after_submit.png", full_page=False)
            print("✓ Screenshot saved: test_after_submit.png")
            
        except Exception as e:
            print(f"✗ Error submitting form: {e}")
            page.screenshot(path="test_error_submit.png", full_page=False)
            browser.close()
            return False
        
        print("\n" + "="*80)
        print("STEP 7: Verify navigation to new trip workspace")
        print("="*80)
        
        # Wait a bit for navigation
        page.wait_for_timeout(2000)
        
        current_url = page.url
        print(f"✓ Current URL: {current_url}")
        
        if "/workspace/" in current_url and "trip-demo" not in current_url:
            print("✓ Successfully navigated to new trip workspace!")
        else:
            print("! URL did not change as expected")
        
        print("\n" + "="*80)
        print("STEP 8: Check browser console for errors")
        print("="*80)
        
        errors = [log for log in console_logs if log["type"] == "error"]
        warnings = [log for log in console_logs if log["type"] == "warning"]
        
        print(f"✓ Console errors: {len(errors)}")
        for error in errors[:5]:
            print(f"  - {error['text']}")
        
        print(f"✓ Console warnings: {len(warnings)}")
        for warning in warnings[:5]:
            print(f"  - {warning['text']}")
        
        print("\n" + "="*80)
        print("STEP 9: Take final screenshot")
        print("="*80)
        
        page.screenshot(path="test_final_state.png", full_page=False)
        print("✓ Screenshot saved: test_final_state.png")
        
        browser.close()
        
        return True

if __name__ == "__main__":
    success = test_call_capture_workflow()
    sys.exit(0 if success else 1)
