import time
import os
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def harvest_exam_urls_all_pages(driver, button_selector):
    wait = WebDriverWait(driver, 15)
    
    # We will now store a tuple of (date, url)
    all_exam_data = [] 
    # A set to keep track of dates we've already seen
    seen_dates = set() 
    
    page_number = 1
    
    print("\nStarting the multi-page harvest...")
    
    while True:
        print(f"--- Harvesting Page {page_number} ---")
        
        try:
            buttons = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, button_selector))
            )
            
            for button in buttons:
                onclick_text = button.get_attribute("onclick")
                pdf_path = onclick_text.split("'")[1]
                
                # EXTRACT THE DATE: Splits '/20251113/go3/...' and grabs '20251113'
                exam_date = pdf_path.split('/')[1][:8]
                exam_year = exam_date[:4]

                if "enga" in pdf_path:
                    continue
                
                # CHECK FOR DUPLICATES: If we haven't seen this date yet, add it!
                if exam_date not in seen_dates:
                    seen_dates.add(exam_date)
                    full_pdf_url = f"https://wdown.ebsi.co.kr/W61001/01exam{pdf_path}"
                    all_exam_data.append((exam_date, full_pdf_url))
                else:
                    # It's a duplicate (likely the Even/짝수형 version), so we ignore it
                    pass
                
            print(f"Unique exams harvested so far: {len(all_exam_data)}")
            
        except TimeoutException:
            print(f"⚠️ No English buttons found on page {page_number} (or it timed out). Stopping harvest.")
            break 
            
        # [ ... The rest of your page turning logic remains exactly the same ... ]
        # 2. Look for the exact NEXT page number (e.g., "2", "3", "4")
        next_page_number = page_number + 1
        
        try:
            # ATTEMPT 1: Try to find the exact number link (e.g., "2", "3", "4", "5")
            next_page_link = driver.find_element(By.LINK_TEXT, str(next_page_number))
            print(f"Moving to page {next_page_number}...")
            driver.execute_script("arguments[0].click();", next_page_link)
            
        except NoSuchElementException:
            # ATTEMPT 2: The number isn't visible. It might be hidden in the next pagination block (e.g., page 6).
            # Let's look for the "Next" arrow instead.
            try:
                # Note: You may need to inspect the EBS 'Next' arrow and ensure "a.btn_next" is the correct CSS selector!
                next_arrow = driver.find_element(By.CSS_SELECTOR, "a.btn_next")
                
                print(f"Page {next_page_number} is hidden. Clicking the 'Next Block' arrow...")
                driver.execute_script("arguments[0].click();", next_arrow)
                
            except NoSuchElementException:
                # If there's no number AND no Next arrow, we are truly done.
                print(f"Reached the absolute final page. (Could not find page {next_page_number} or a Next arrow).")
                break

        # 3. Wait for the old buttons to disappear (Confirming the AJAX refresh)
        if buttons:
            try:
                wait.until(EC.staleness_of(buttons[0]))
            except TimeoutException:
                print("Warning: The table didn't seem to refresh. Trying to proceed anyway...")
        
        # Update our tracker to the new page
        page_number = next_page_number
        time.sleep(2) 

    # Steal the cookies before we close the browser
    session_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    
    print(f"\n✅ Master Harvest Complete! Total Unique PDFs found: {len(all_exam_data)}")
    return all_exam_data, session_cookies

def batch_download_pdfs(exam_data_list, session_cookies, save_directory="./csat_pdfs"):
    os.makedirs(save_directory, exist_ok=True)
    
    # We unpack the (date, url) tuple
    for exam_date, url in exam_data_list:
        
        # Name the file using the extracted date!
        filename = f"{exam_date}.pdf"
        filepath = os.path.join(save_directory, filename)
        
        print(f"Downloading {filename}...")
        response = requests.get(url, cookies=session_cookies)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"   -> Saved to {filepath}")
        else:
            print(f"   ❌ Failed with status code: {response.status_code}")
            
    print("🎉 All downloads complete!")

if __name__ == "__main__":
    # 🛑 SECURE VAULT INITIALIZATION
    load_dotenv()
    
    # Pull keys safely from .env
    secure_hschsp = os.getenv("EBS_HSCHSP_ID")
    secure_oauth = os.getenv("EBS_OAUTH_TOKEN")
    secure_pcid = os.getenv("EBS_PCID")

    # --- MAIN EXECUTION ---
    # Setup your webdriver (Chrome/Edge)
    driver = webdriver.Chrome() 
    
    # 1. Establish Domain & Inject Cookies
    driver.get("https://www.ebsi.co.kr")
    
    # Safely inject the cookies using the hidden variables
    if secure_hschsp:
        driver.add_cookie({'name': 'HSCHSP_ID', 'value': secure_hschsp, 'domain': '.ebsi.co.kr'})
    if secure_oauth:
        driver.add_cookie({'name': 'OAuth_Token_Request_State', 'value': secure_oauth, 'domain': '.ebsi.co.kr'})
    if secure_pcid:
        driver.add_cookie({'name': 'PCID', 'value': secure_pcid, 'domain': '.ebsi.co.kr'})
    
    # 2. Navigate to Target Search Page
    target_url = "https://www.ebsi.co.kr/ebs/xip/xipc/previousPaperList.ebs?targetCd=D300"
    driver.get(target_url)
    
    input("Press Enter in the console once you have manually filtered the table and are ready to harvest...")
    
    # 3. Harvest URLs (Targeting the 'English Question' button)
    button_css = "button[onclick*='eng_1_mun_'], button[onclick*='eng_mun'], button[onclick*='eng1_mun'], button[onclick*='engb_mun'], button[onclick*='engb1_mun']"
    urls_to_download, stolen_cookies = harvest_exam_urls_all_pages(driver, button_css)
    
    # 4. Close Heavy Browser & Start Silent Download
    driver.quit()
    pdf_path = os.getenv("PDF_PATH")
    my_folder = pdf_path
    batch_download_pdfs(urls_to_download, stolen_cookies, save_directory=my_folder)