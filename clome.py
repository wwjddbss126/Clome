import re
import time
import json
import requests
import unicodedata
import time
import datetime
import N_MYBOXClient as n

from colorama import Fore, Style
from itertools import product
from playwright.sync_api import (Locator, Page, sync_playwright, Playwright, BrowserType)   
from tabulate import tabulate
from mega import Mega


urls = {

    "megalogin": "https://mega.nz/login",
    "navermain": "https://naver.com",
    "keybackup": "https://mega.nz/keybackup",
    "myboxmain": "https://photo.mybox.naver.com/",
    "naversecurity": "https://nid.naver.com/user2/help/myInfoV2?m=viewSecurity",
    "naverapi": "https://github.com/wwjddbss126/NaverMYBOX.git"    
}

tera_urls = {

    "user": "https://www.terabox.com/passport/get_info",
    "account": "https://www.terabox.com/rest/2.0/membership/proxy/user?clientfrom=h5&method=query&membership_version=1.0",
    "list": "https://www.terabox.com/api/list",
    "thumbnail": "https://www.terabox.com/api/list?app_id=250528&web=1&channel=dubox&clienttype=5& \
        jsToken=66D9D25B43BAD5980B35B9D195A431B533884FDD859199C8D8A31171BB36CC878019D1A1AC8BD95CF7 \
        F3B9F12330EFA4C413C8FB19847AE063C51A292ED6A82C&order=time&desc=1&dir=%2F&num=100&page=1&showempty=0",
    "data": "https://www.terabox.com/api/download?app_id=250528&web=1&channel=dubox&clienttype=5& \
        jsToken=66D9D25B43BAD5980B35B9D195A431B533884FDD859199C8D8A31171BB36CC878019D1A1AC8BD95CF7F3B9F12330EFA4C413C8FB19847AE063C51A292ED6A82C"
}

patterns_mega = [  

    r"https:\/\/g\.api\.mega\.co\.nz\/(?:wsc\/[a-zA-Z0-9-]{43}\?|cs\?id=-\d+&|sc\?id=-\d+&).*?sid=([a-zA-Z0-9\-_]{58})",
    r"https:\/\/mega\.nz..k\+.(\[(?:-?\d{4,},){3}-?\d{4,}\])"    
]

patterns_mybox = [  

    r"(?:NID_SES.{9}|{\"name\":\"NID_SES\",\"value\":\"|NID_SES=)([A-Za-z0-9+/=]{500,})(?:\"|;|)",
    r"(?:NID_AUT.{9}|{\"name\":\"NID_AUT\",\"value\":\"|NID_AUT=)([A-Za-z0-9+/]{64})(?:\"|;|)"    
]
 
patterns_terabox = [  

    r"ndus=([a-zA-Z0-9_]{40});"
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
    
    if len(result) == 1:  # If the result has only one key
        combination = list(combination[0])  # Convert the tuple to a list
            
    print("\n")
    log_info("================  Search Result Ends  ================\n")
    log_debug("Start finding valid keys...")
        
    return combination    
    

def login_terabox(data_list):
    for i in data_list:
        response = requests.get(tera_urls["user"], cookies={'ndus': i})
        
        if response.status_code == 200:
            resp = json.loads(response.content)
            log_info("Login Succeed!")
            log_info("User Name: {}".format(resp['data']['display_name']))
            log_info("Profile Image URL: {}".format(resp['data']['head_url']))
            print("\n")
            
            while(1):
                n = display_terabox()
                if n == 0:
                    log_info("[*] End Script...")
                    break
                if n == 1: # 계정 멤버십 정보
                    url, key = tera_urls["account"], "data"
                    resp = json.loads(requests.get(url, cookies={'ndus': i}).content)
                    
                    for key, value in resp.items():
                        if isinstance(value, dict):
                            print(key)
                            for sub_key, sub_value in value.items():
                                print(f"{sub_key}: {sub_value}")
                            print()
                        else:
                            print(f"{key}: {value}")           
                    
                elif n == 2: # 파일 메타데이터
                    url, key = tera_urls["list"], "list"
                    headers = ['category', 'isdir', 'md5', 'oper_id', 'fs_id', 'server_atime', 'server_ctime', 'local_mtime', 'size', 'share', 'pl', 'path', 'local_ctime', 'server_filename', 'server_mtime', 'owner_id']
                    
                    resp = json.loads(requests.get(url, cookies={'ndus': i}).content)               
                    table_data = []  

                    for item in resp[key]:
                        row = []
                        for key in headers:
                            value = item.get(key)
                            if isinstance(value, str) and any(ord(c) > 127 for c in value):
                                value = unicodedata.normalize('NFC', value)
                            row.append(value)
                        table_data.append(row)
                        
                    table = tabulate(table_data, headers=headers, tablefmt='grid')
                    print(table)

                elif n == 3: # 썸네일 URL
                    url, key = tera_urls["thumbnail"], "list"

                    resp = json.loads(requests.get(url, cookies={'ndus': i}).content)

                    for item in resp[key]:
                        res = []
                        res.append(item['isdir'])
                        res.append(item['md5'])

                        value = item['path']
                        if isinstance(value, str) and any(ord(c) > 127 for c in value):
                            value = unicodedata.normalize('NFC', value)
                        res.append(value)

                        res.append(item['size'])
                        try:
                            res.append(item['thumbs'])
                        except:
                            res.append("null")

                        print('-' * 80)
                        print('isdir:', res[0])
                        print('md5:', res[1])
                        print('path:', res[2])
                        print('size:', res[3])
                        print('thumbs:', res[4])

                elif n == 4: # 파일 데이터
                    url, key = tera_urls["data"], "dlink"

                    dp_id = "&dp-logid=17867300236566300015"
                    fs_id = "&fidlist=%5B" + "767620573048020" + "%5D"
                    ts = "&timestamp=" + str(round(time.time()))
                    bds = "&bdstoken=" + "9bb0ee320bb560ed7685046a3cfca8d2"

                    url = url + dp_id + fs_id + "&type=dlink&vip=2&sign=dwN8Qn3b7PID7pY9j5zy%2FyfZ7mytKZaOaFcqNctgtBMaByNcoA7iNA%3D%3D" + ts + bds
                    resp = json.loads(requests.get(url, cookies={'ndus': i}).content)
                    print(url)
                    print(resp)
                
                else:
                    log_debug("You entered wrong #.")
                    break               
                
        else:
            print(i)
            log_info("Login Faild {} :(".format(response.status_code))

def display_terabox():
    log_info("[*] Enter #. to explore TeraBox...")
    log_info("#1: Show Membership Information")
    log_info("#2: Show File list")
    log_info("#3: Show Thumbnail Information")
    log_info("#4: Download file (Not surpported now, To be continued ...)")
    print("\n")
    return int(input("Enter #."))
    
def display_mega():
    log_info("[*] Enter #. to explore MEGA Cloud...")
    log_info("#0: Exit")
    log_info("#1: Show User & Membership Information")
    log_info("#2: Show File list")
    log_info("#3: Show Thumbnail Information or Download file")
    print("\n")
    return int(input("Enter #."))

def display_mybox():
    log_info("[*] Enter #. to explore TeraBox...")
    log_info("#1: Show User & Storage resousrce Information")
    log_info("#2: Show File list")
    log_info("#3: Show Thumbnail Information")
    log_info("#4: Download file")
    log_info("#5: Search File (Keyword Search, Advanced Search)")
    print("\n")
    return int(input("Enter #."))

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
                    log_info("[*] Do you want to reset password using Recovery Key? (y/n)")
                    rk = input()
                    if rk in ["y", "Y"]:
                        page.goto(urls["keybackup"])
                        
                        time.sleep(2)
                        backup_keyinput = page.query_selector("#backup_keyinput")
                        
                        if backup_keyinput:
                            res = backup_keyinput.get_attribute("value")
                            log_info(f"Recovery Key: {res}")
                            log_info("Now, you can reset password to to prevent anti-forensic behavior and to permanently access it.")
                            
                            log_info("If you've got an ID and PW, you can now log in!")
                            log_info("[*] Will you use the Internal API feature for cloud storage navigation? (y/n)")
                            display_api("MEGA")
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
        
        log_info("[*] End Script...")  
        if browser:
            browser.close()

def display_api(service):
    log_info("Did you get the ID, PW? (y/n)")   
    while(1):
        a = input()
        if a in ["y", "Y"]:
            log_info("[*] Enter ID or Email")
            id = input()
            log_info("[*] Enter PW")
            pw = input()
            if service == "MEGA":
                api_mega(id, pw)
            if service == "MYBOX":
                api_mybox(id, pw)
            break

        elif a in ["n", "N"]:
            log_info("[*] End Script...")                     
            break

        else:
            log_info("Enter y or n !!")

def api_mybox(id, pw):
    try:
        with sync_playwright() as playwright:
            n.login(playwright, id, pw)
    except:
        log_error("[*] User Authentication Failed")

    while 1:
        num = display_mega()
        if num == 0:
            log_debug("[*] End Script...")
            exit(-1)
        if num == 1:
            log_debug("[*] Collecting User Resource Information...")
            n.user()
        if num == 2:
            log_debug("[*] Collecting File Resource Information...")
            n.file_list()
        if num == 3:
            log_debug("[*] Collecting File Thumbnail...")
            n.file_thumb()
        if num == 4:
            log_debug("[*] Collecting File Data...")
            n.file_data()
        if num == 5:
            print(
            """
            0. Exit
            1. Keyword Search
            2. Advanced Search
            """)
            searchnum = int(input())
            if searchnum == 0:
                log_debug("[*] Exit...")
                pass
            if searchnum == 1:
                log_info("[*] Keyword Search: Enter Keyword to search")
                keyword = input()
                log_debug("[*] Searching File...")
                n.file_search(keyword)
            if searchnum == 2:
                n.file_search_adv_options()

def api_mega(id, pw):
    mega = Mega()
    try:
        m = mega.login(id, pw)        
        while(1):
            n = display_mega()
            if n == 0:
                log_info("[*] Exit...")
                break
            if n == 1: # 계정 정보
                res = m.get_user()
                print(f"Date of subscription: {datetime.datetime.fromtimestamp(res['since']).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"User email: {res['email']}")
                print(f"User name: {res['name']}")
                res = m.get_storage_space(kilo=True)
                print(f"Used space: {res['used']}")
                print(f"Total space: {res['total']}")
            if n == 2: # 파일 리스트
                resp = m.get_files()
                output = []
                for key, value in resp.items():
                    name = value["a"] if isinstance(value.get("a"), str) else value.get("a", {}).get("n", "-")
                    item = {
                        "name": name.encode('latin1').decode('utf-8'),
                        "id": key,
                        "size": value.get("s", "-"),
                        "type": value.get("t", "-"),
                        "is_trashed": value["a"] if isinstance(value.get("a"), str) else value.get("a", {}).get("rr", "X"),
                        "owner": value.get("u", "-"),
                        "createdtime": value.get("ts", "-")
                    }
                    output.append(item)

                table_headers = ["Name", "ID", "Size", "Type", "Is Trashed", "Owner", "Created Time"]
                table_data = [[item["name"], item["id"], item["size"], item["type"], item["is_trashed"], item["owner"], item["createdtime"]] for item in output]

                print(tabulate(table_data, headers=table_headers))               

            if n == 3: # 썸네일 조회 & 파일 다운로드
                log_info("[*] Enter file name to view thumbnail or download")
                log_info("[*] Currently, only features for files that have not been deleted are supported.")
                name = input()
                link = m.export(name)
                print(link)

    except:
        log_error("Login Faild :(")

if __name__ == '__main__':
    log_info("Have you obtained the ID, PW of the cloud storage account you want to explore? Enter 1 if correct, or 2 if not.")
    fnum = int(input())
    if fnum == 1:
        log_info("#1: Mega Cloud")
        log_info("#2: Naver MYBOX")
        num = int(input())
        if num == 0:
            log_info("[*] End Script...")
            exit(-1)
                    
        if num == 1:
            display_api("MEGA")
            
        if num == 2:
            display_api("MYBOX")

    if fnum == 2:
        file_path = str(input("Input Memory Image Path: "))
        
        log_info("#1: Mega Cloud")
        log_info("#2: Naver MYBOX")
        log_info("#3: TeraBox")
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
        
        if num == 3:
            log_info("[*] Find significant values using findall() in TeraBox...")
            start = time.time()                    
            result = find_findall(file_path, patterns_terabox)
            
            log_debug(f"Elapsed time : {time.time() - start}")            
            login_terabox(print_result(result))