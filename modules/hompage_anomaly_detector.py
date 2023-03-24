from datetime import datetime
import sys
from urllib import parse

from bs4 import BeautifulSoup
import lxml
import requests


sys.setrecursionlimit(5000)


class LoginError(Exception):
    def __init__(self):
        super().__init__("[-] Login failed!")
        

class OfficialAnnouncementChangeDetector:
    def __init__(self, user_id: str, user_pw: str, target_url_list: list, session: requests.Session=None):
        if session:
            self.__session = session
        else:
            self.__session = self.__login(user_id, user_pw)
        self.__target_url_list = target_url_list
        self.__before_post_information_dict = None
    
    def __del__(self):
        pass
    
    def __login(self, user_id, user_pw):
        session = requests.session()
        
        login_url = "https://login.com/"
        login_data = {
			"id": user_id,
			"pw": user_pw
		}
        session = requests.Session()
        response = session.post(login_url, datas=login_data, allow_redirects=False, verify=False)
        if response.text:
            raise LoginError
        else:
            return session
    
    def __get_post_details(self, post_url: list) -> [list, str]:
        attachment_urls = []
        base_url = parse.urlparse(post_url)
        base_url = f"{base_url.scheme}://{base_url.netloc}"
        response = self.__session.get(post_url, verify=False)
        if response.status_code != 200:
            return False
        soup = BeautifulSoup(response.text, "lxml")
        for attachment in soup.select("div#contentView > div.program > table.boardDetail > tbody > tr:nth-child(4) > td > a"):
            attachment_url = parse.urljoin(base_url, attachment.get("href"))
            attachment_urls.append(attachment_url)
        
        contents = soup.select_one("div#contentView > div.program > table.boardDetail > tbody")
        
        # src URL = Base URL + src URL
        for src_attribute in contents.select_one("tr > td.contentBody").select("[src]"):
            src_attribute["src"] = parse.urljoin(base_url, src_attribute.get("src"))
        _contents = str(contents.select_one("tr > td.contentBody"))
        
        contents_dict = {
            "title": contents.select_one("tr:nth-child(1) > td").text,
            "time": contents.select_one("tr:nth-child(2) > td:nth-child(2)").text,
            "author": contents.select_one("tr:nth-child(3) > td").text,
            "attachemnts": "\n".join(a_tag.text for a_tag in contents.select("tr:nth-child(4) > td > a")),
            "contents": _contents,
        }
        return attachment_urls, contents_dict
    
    def __get_post_informations(self) -> dict:
        post_information_dict = {}
        for target_url in self.__target_url_list:
            target_base_url = parse.urlparse(target_url)
            unit = target_base_url.netloc.split(".")[0]
            target_base_url = f"{target_base_url.scheme}://{target_base_url.netloc}"
            response = self.__session.get(target_url, verify=False)
            if response.status_code != 200:
                return False
            soup = BeautifulSoup(response.text, "html.parser")
            for post in soup.select("div#contentView > div.program > form > table.boardList > tbody > tr > td.title > a"):
                post_title = post.get("title")
                post_url = parse.urljoin(target_base_url, post.get("href"))
                attachment_url, contents = self.__get_post_details(post_url)
                post_information_dict[post_url] = {
                    "unit": unit, 
                    "title": post_title,
                    "attachment_url": attachment_url,
                    "contents": contents
                }
        return post_information_dict
    
    def detect_official_announcement_change(self) -> list:
        post_change_result = []
        if not self.__before_post_information_dict:
            self.__before_post_information_dict = self.__get_post_informations()
        else:
            current_post_information_dict = self.__get_post_informations()
            for current_post_url in current_post_information_dict:
                # If post is appended
                if current_post_url not in self.__before_post_information_dict:
                    post_change_result.append({
                        "url": current_post_url,
                        "unit": current_post_information_dict.get(current_post_url).get("unit"),
                        "type": "post_append",
                        "title": current_post_information_dict.get(current_post_url).get("title"),
                        "contents": current_post_information_dict.get(current_post_url).get("contents")
                    })
                    continue
                
                # If attachment's URL is appended
                changed_attachment_url = []
                before_post_attachment_url_list = self.__before_post_information_dict.get(current_post_url).get("attachment_url")
                current_post_attachment_url_list = current_post_information_dict.get(current_post_url).get("attachment_url")
                for current_post_attachment_url in current_post_attachment_url_list:
                    if current_post_attachment_url not in before_post_attachment_url_list:
                        changed_attachment_url.append(current_post_attachment_url)
                
                if changed_attachment_url:
                    post_change_result.append({
                        "url": current_post_url,
                        "unit": current_post_information_dict.get(current_post_url).get("unit"),
                        "type": "attachment_append",
                        "title": current_post_information_dict.get(current_post_url).get("title"),
                        "attachment": changed_attachment_url,
                        "contents": current_post_information_dict.get(current_post_url).get("contents")
                    })
                
                # If attachment's URL is deleted
                changed_attachment_url = []
                for before_post_attachment_url in before_post_attachment_url_list:
                    if before_post_attachment_url not in current_post_attachment_url_list:
                        changed_attachment_url.append(before_post_attachment_url)
                if changed_attachment_url:
                    post_change_result.append({
                        "url": current_post_url,
                        "unit": self.__before_post_information_dict.get(current_post_url).get("unit"),
                        "type": "attachment_delete",
                        "title": self.__before_post_information_dict.get(current_post_url).get("title"),
                        "attachment": changed_attachment_url,
                        "contents": self.__before_post_information_dict.get(current_post_url).get("contents")
                    })
            # If post is deleted
            for before_post_url in self.__before_post_information_dict:
                if before_post_url not in current_post_information_dict:
                    post_change_result.append({
                        "url": before_post_url,
                        "unit": self.__before_post_information_dict.get(before_post_url).get("unit"),
                        "type": "post_delete",
                        "title": self.__before_post_information_dict.get(before_post_url).get("title"),
                        "contents": self.__before_post_information_dict.get(before_post_url).get("contents")
                    })
            
            self.__before_post_information_dict = current_post_information_dict
        return post_change_result

             
class URLChangeDetector:
    def __init__(self, user_id: str, user_pw: str, target_url_list: list, session: requests.Session=None):
        if session:
            self.__session = session
        else:
            self.__session = self.__login(user_id, user_pw)
        self.__target_url_list = target_url_list
        self.__before_url_dict = None
    
    def __del__(self):
        pass
    
    def __login(self, user_id, user_pw):
        session = requests.session()
        
        login_url = "https://login.com/"
        login_data = {
			"id": user_id,
			"pw": user_pw
		}
        session = requests.Session()
        response = session.post(login_url, datas=login_data, allow_redirects=False, verify=False)
        if response.text:
            raise LoginError
        else:
            return session
    
    def __get_url_dict(self) -> dict:
        url_dict = {}
        for target_url in self.__target_url_list:
            target_base_url = parse.urlparse(target_url)
            # unit(부대)는 도메인명에 포함되어있음
            unit = target_base_url.netloc.split(".")[0]
            target_base_url = f"{target_base_url.scheme}://{target_base_url.netloc}"
            temp_url_list = []
            response = self.__session.get(target_url, verify=False)
            if response.status_code != 200:
                return False
            
            soup = BeautifulSoup(response.text, "lxml")
            for tag in soup.select("[href]"):
                # If "href" attribute not exist -> continue
                if not tag.has_attr("href"):
                    continue
                
                url = tag.get("href")
                if url.startswith("#"):
                    continue
                if url.startswith("javascript"):
                    continue
                
                # Join base url with url's path and query
                if url.startswith("/"):
                    url = parse.urljoin(target_base_url, url)
                temp_url_list.append(url)
            url_dict[unit] = temp_url_list
            
        return url_dict
    
    # __get_url_dict 에서 얻은 페이지의 기본값을 바탕으로 변경사항 확인
    def detect_url_change(self) -> list:
        url_change_result = []
        if not self.__before_url_dict:
            self.__before_url_dict = self.__get_url_dict()
        else:
            current_url_dict = self.__get_url_dict()
            if not current_url_dict:
                return False
            for unit in current_url_dict:
                for current_url in current_url_dict.get(unit):
                    # If URL is appended
                    if not current_url in self.__before_url_dict.get(unit):
                        url_change_result.append({
                            "url": current_url,
                            "unit": unit,
                            "type": "url_append"
                        })
                
            for unit in self.__before_url_dict:
                # If URL is deleted
                for before_url in self.__before_url_dict.get(unit):
                    if not before_url in current_url_dict.get(unit):
                        url_change_result.append({
                            "url": before_url,
                            "unit": unit,
                            "type": "url_delete"
                        })
            self.__before_url_dict = current_url_dict
        return url_change_result