import time
import os
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def parse_answer_button(onclick_text):
    """
    Handles EBS's answer formats, heavily prioritizing the J and J2 formats
    that EBS uses for answer keys.
    """
    # 1. The dominant format: goDownLoadJ
    if "goDownLoadJ(" in onclick_text:
        raw_url = onclick_text.split("'")[1]
        url = raw_url
        
        # Extracts from: 'https://wdown.../01exam/20260604/mobile/...'
        date = raw_url.split('/')[5][:8] 
        
        # Safely grabs .png or .jpg
        ext = raw_url[-4:] 
        return url, ext, date
    
    # 2. The older format: goDownLoadJ2
    elif "goDownLoadJ2" in onclick_text:
        raw_path = onclick_text.split("'")[1]
        url = f"https://wdown.ebsi.co.kr/W61001/01exam{raw_path}"
        date = raw_path.split('/')[1][:8] 
        ext = ".pdf" if ".pdf" in raw_path else raw_path[-4:]
        return url, ext, date
        
    return None, None, None

def harvest_answer_urls(driver):
    wait = WebDriverWait(driver, 15)
    print("Harvesting elements...")
    
    # We will now store a tuple of (date, url)
    all_answers_data = [] 
    # A set to keep track of dates we've already seen
    seen_dates = set() 
    page_number = 1
    
    print("\nStarting the Answer harvest...")

    while True:
        try:
            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "button")))
        except TimeoutException:
            break

        all_bts = driver.find_elements(By.TAG_NAME, "button")

        ans_bts = [b for b in all_bts if "정답" in b.text]
    
        for btn in ans_bts:
            try:
                onclick_text = btn.get_attribute("onclick")
                if not onclick_text: continue
            
                a_url, a_ext, exam_date = parse_answer_button(onclick_text)
            
                if a_url and exam_date and exam_date not in seen_dates:
                    seen_dates.add(exam_date)
                    all_answers_data.append((exam_date, a_url, a_ext))
                    print(f"✅ 정답지 발견: {exam_date}")
            except Exception as e:
                continue
            
    
        # [ ... The rest of your page turning logic remains exactly the same ... ]
        # 2. Look for the exact NEXT page number (e.g., "2", "3", "4")
        next_page_number = page_number + 1
        
        # 만약 버튼이 하나도 없었다면 None으로 처리
        watch_button = ans_bts[0] if ans_bts else None

        next_found = False
        try:
            next_page_link = driver.find_element(By.LINK_TEXT, str(next_page_number))
            driver.execute_script("arguments[0].click();", next_page_link)
            next_found = True
        except NoSuchElementException:
            try:
                next_arrow = driver.find_element(By.CSS_SELECTOR, "a.btn_next")
                driver.execute_script("arguments[0].click();", next_arrow)
                next_found = True
            except NoSuchElementException:
                print("No more pages.")
                break

        if next_found:
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_elements(By.TAG_NAME, "button") != watch_button
                )
            except TimeoutException:
                print("Proceed.")
        
        page_number = next_page_number
        time.sleep(2)
    
    session_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    
    print(f"\n✅ Master Harvest Complete! Total Unique PDFs found: {len(all_answers_data)}")
    return all_answers_data, session_cookies

def batch_download_pdfs(answer_data_list, session_cookies, save_directory):
    os.makedirs(save_directory, exist_ok=True)
    
    # We unpack the (date, url) tuple
    for exam_date, url, ext in answer_data_list:
        
        # Name the file using the extracted date!
        filename = f"{exam_date}_A{ext}"
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
    if secure_hschsp: driver.add_cookie({'name': 'HSCHSP_ID', 'value': secure_hschsp, 'domain': '.ebsi.co.kr'})
    if secure_oauth: driver.add_cookie({'name': 'OAuth_Token_Request_State', 'value': secure_oauth, 'domain': '.ebsi.co.kr'})
    if secure_pcid: driver.add_cookie({'name': 'PCID', 'value': secure_pcid, 'domain': '.ebsi.co.kr'})
    
    # 2. Navigate to Target Search Page
    target_url = "https://www.ebsi.co.kr/ebs/xip/xipc/previousPaperList.ebs?targetCd=D300"
    driver.get(target_url)
    
    input("Press Enter in the console once you have manually filtered the table and are ready to harvest...")
    
    # 3. Harvest URLs (Targeting the 'English Question' button)
    urls_to_download, stolen_cookies = harvest_answer_urls(driver)
    
    # 4. Close Heavy Browser & Start Silent Download
    driver.quit()
    pdf_path = os.getenv("ANS_PATH")
    batch_download_pdfs(urls_to_download, stolen_cookies, save_directory=pdf_path)