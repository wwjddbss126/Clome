import re
import time
import json

from colorama import Fore, Style
from itertools import product
from playwright.sync_api import sync_playwright

urls = {
    "megalogin": "https://mega.nz/login",
    "navermain": "https://naver.com",
    "keybackup": "https://mega.nz/keybackup",
    "myboxmain": "https://photo.mybox.naver.com/",
    "naversecurity": "https://nid.naver.com/user2/help/myInfoV2?m=viewSecurity",
    "naverapi": "https://github.com/wwjddbss126/NaverMYBOX.git"
}

patterns_mega = [  

    r"https:\/\/g\.api\.mega\.co\.nz\/(?:wsc\/[a-zA-Z0-9-]{43}\?|cs\?id=-\d+&|sc\?id=-\d+&).*?sid=([a-zA-Z0-9\-_]{58})",
    r"https:\/\/mega\.nz..k\+.(\[(?:-?\d{4,},){3}-?\d{4,}\])"
    
]

patterns_mybox = [  

    r"(?:NID_SES.{9}|{\"name\":\"NID_SES\",\"value\":\"|NID_SES=)([A-Za-z0-9+/=]{500,})(?:\"|;|)",
    r"(?:NID_AUT.{9}|{\"name\":\"NID_AUT\",\"value\":\"|NID_AUT=)([A-Za-z0-9+/]{64})(?:\"|;|)"
    
]
    
def log_info(message):
    print(Fore.LIGHTBLUE_EX + f"[INFO] {message}" + Style.RESET_ALL)


def log_debug(message):
    print(Fore.GREEN + f"[DEBUG] {message}" + Style.RESET_ALL)


def log_error(message):
    print(Fore.RED + f"[ERROR] {message}" + Style.RESET_ALL)


def find_findall(file_path, patterns):
    matches = {pattern: [] for pattern in patterns}

    with open(file_path, 'rb') as file:
        chunk_size = 1024 * 1024 * 1024
        offset = 0

        while True:
            file.seek(offset)
            chunk = file.read(chunk_size).decode(errors='ignore')

            if not chunk:
                break

            for pattern in patterns:
                pattern_matches = re.findall(pattern, chunk)

                for match in pattern_matches:
                    if match not in matches[pattern]:
                        matches[pattern].append(match)                        
                        log_debug(f"Found match for {pattern}: {match}")
            offset += len(chunk)
            log_debug(f"Processed: {offset} bytes")

    return matches


def print_result(result):
    log_info("================ Search Result Starts ================")
    
    for key, value in result.items():
        
        if value:        
            print(f"\nPattern: {key}")
            for v in value:
                print(f"{v}")    
        else:
            log_info(f"Value Not Found :( Not Found Pattern: {key}")
            log_debug("Exiting the script...")
            exit(-1)
    
    combination = []
    v_c = product(*(value for key, value in result.items()))
    for c in v_c:
        combination.append(c)
            
    print("\n")
    log_info("================  Search Result Ends  ================\n")
    log_debug("Starting Playwright to find valid keys...")
        
    return combination

def login_mybox(data_list):
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        browser = browser_type.launch(headless=False)
        page = browser.new_page()

        page.goto(urls["navermain"])
        time.sleep(3)
        
        for data in data_list:
            ses, aut = data[0], data[1]
            
            log_info("Try:" + ses + ", " + aut)
            page.evaluate(f"document.cookie = 'NID_SES={ses}; domain=.naver.com';")
            page.evaluate(f"document.cookie = 'NID_AUT={aut}; domain=.naver.com';")
            
            time.sleep(10)
            
            page.reload()            
            time.sleep(2)
            
            # element1 = page.query_selector('#account > div > a')
            element2 = page.query_selector('#account > div.MyView-module__my_info___GNmHz > div > button')
            
            if element2:                     
                
                log_info("Finally You've got the keys!")
                log_debug(f"Valid keys: {data}")
                
                page.goto(urls["myboxmain"])
                                
                element = page.query_selector('#gnb_my_lyr > div.gnb_my_content > div.gnb_txt_area > a')
                log_debug(f"I've found additional infos: User ID would be {element.text_content()}")
                
                while(1):
                    log_info("Do you want to reset password and using Internal API to collect data? (y/n)")
                    api = input()
                    if api in ["y", "Y"]:                        
                        page.goto(urls["naversecurity"])
                        log_info("Now you can rest password to prevent Anti-Forensic from suspects")
                        url = urls["naverapi"]
                        log_info(f"Also after changing password, you can use Naver Internal API: {url}")
                        break

                    elif api in ["n", "N"]:
                        log_info("You can navigate Naver MYBOX Storage Freely!")                        
                                                
                    else:
                        log_info("Enter y or n !!")                    
                                           
            else:
                log_debug("Key Invalid :( Clearing all values...")          
                page.context.clear_cookies()
            
        log_info("Ending Tool...")
        if browser:
            browser.close()
            
def login_mega(data_list):
    with sync_playwright() as playwright:
        browser_type = playwright.chromium
        browser = browser_type.launch(headless=False)
        page = browser.new_page()

        page.goto(urls["megalogin"])
        time.sleep(3)
        
        for data in data_list:
            sid, k = data[0], data[1]
            
            log_info("Try:" + sid + ", " + k)
            page.evaluate(f"localStorage.setItem('sid', '{sid}');")
            page.evaluate(f"localStorage.setItem('k', '{k}');")
            
            page.reload()            
            time.sleep(2)
            
            handle_value = page.evaluate('localStorage.getItem("handle")')
            
            if handle_value:
                log_debug(f"I've found additional infos: User ID would be {handle_value}")
                
                try:
                    privk_value = page.evaluate('localStorage.getItem("privk")')
                    log_debug(f"I've found additional infos: User's Private Key would be {privk_value}")
                except:
                    log_debug("Private Key Not Found")
                
                log_info("Finally You've got the keys!")
                log_debug(f"Valid keys: {data}")
                
                while(1):
                    log_info("Do you want to reset password using Recovery Key? (y/n)")
                    rk = input()
                    if rk in ["y", "Y"]:
                        page.goto(urls["keybackup"])
                        
                        time.sleep(2)
                        backup_keyinput = page.query_selector("#backup_keyinput")
                        
                        if backup_keyinput:
                            res = backup_keyinput.get_attribute("value")
                            log_info(f"Recovery Key: {res}")
                        else:
                            log_info("Recovery Key not found :(")

                        browser.close()
                        break

                    elif rk in ["n", "N"]:
                        log_info("You can navigate MEGA Cloud Storage Freely!")                        
                                               
                    else:
                        log_info("Enter y or n !!")
            else:                
                log_debug("Key Invalid :( Clearing all values...")
                page.evaluate('localStorage.clear()')
        
        log_info("Ending Tool...")
        if browser:
            browser.close()

if __name__ == '__main__':
    file_path = str(input("Input Memory Image Path: "))
    
    log_info("#1: Mega Cloud")
    log_info("#2: Naver MYBOX")
    num = int(input())
    
    if num == 0:
        log_info("[*] End Script...")
        exit(-1)
                
    if num == 1:
        log_info("[*] Find significant values using findall() in MEGA Cloud...") 
        start = time.time()        
        result = find_findall(file_path, patterns_mega)
        
        log_debug(f"Elapsed time : {time.time() - start}")
        login_mega(print_result(result))
        
    if num == 2:
        log_info("[*] Find significant values using findall() in Naver MYBOX...")
        start = time.time()                    
        result = find_findall(file_path, patterns_mybox)
        
        log_debug(f"Elapsed time : {time.time() - start}")
        login_mybox(print_result(result))
        
    