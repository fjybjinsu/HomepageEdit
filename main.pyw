from datetime import datetime
import os
import shutil
import sys

from pyqt5 import uic
from pyqt5.Qt import QDesktopServices, QUrl
from pyqt5.QtCore import *
from pyqt5.QtGui import *
from pyqt5.QtTest import *
from pyqt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from pyqt5.QtWidgets import *
import requests

from modules.hompage_anomaly_detector import OfficialAnnouncementChangeDetector, URLChangeDetector


"""
동일한 PC에서 2개 이상의 QWebEngineView 사용 시 출력되는 오류 로그 출력 방지

[51168:46820:0209/114754.838:ERROR:cache_util_win.cc(20)] Unable to move the cache: 5
[51168:46820:0209/114754.838:ERROR:cache_util.cc(134)] Unable to move cache folder C:\\Users\\USER\\AppData\\Local\\python\\QtWebEngine\\Default\\GPUCache to C:\\Users\\USER\\AppData\\Local\\python\\QtWebEngine\\Default\\old_GPUCache_000
[51168:46820:0209/114754.840:ERROR:cache_creator.cc(134)] Unable to create cache
[51168:46820:0209/114754.840:ERROR:shader_disk_cache.cc(570)] Shader Cache Creation failed: -2
"""
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"

# requests 모듈 InsecureRequestWarning 에러 출력 방지
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# UI파일 연결
login_dialog_class = uic.loadUiType("resources\\login.ui")[0] # 로그인 입력창 UI
main_window_class = uic.loadUiType("resources\\main.ui")[0] # 프로그램 전체 UI
post_widget_class = uic.loadUiType("resources\\post.ui")[0] # 사이트별 표시 위젯 UI

# QDialog 상속(팝업 창과 같은 짧은 기간의 일)
class LoginClass(QDialog, login_dialog_class):
    def __init__(self):
        super().__init__()
        self.__session = None
        self.setupUi(self)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.pushButton.clicked.connect(self.try_login)
    
    def __del__(self):
        pass
    
    # 로그인 시도 메소드
    # 사용자로부터 ID, PW를 입력받은 다음 결과창의 응답 값
    def try_login(self):
        user_homepage_id = self.homepage_id_lineEdit.text()
        user_homepage_pw = self.homepage_pw_lineEdit.text()
        
        login_url = "https://login.com/"
        login_data = {
			"id": user_homepage_id,
			"pw": user_homepage_pw
		}
        session = requests.Session()
        response = session.post(login_url, datas=login_data, allow_redirects=False, verify=False)
        # 로그인 실패 시 프로그램 종료
        if response.text:
            QMessageBox.warning(self, 'Login Fail', '홈페이지 로그인 실패\t')
            qApp.exit(0)
            return
        # __session 변수에 현재의 세션을 저장
        self.__session = session
        QMessageBox.about(self, 'Login Success', '로그인 성공\t')
        qApp.exit(1)
    
    # 현재의 세션을 반환
    def get_session(self):
        return self.__session


class Worker(QThread):
    # 각각의 사이트들에서 수행하는 기능이 동일하므로 pyqtSignal 데코레이터 지정
    # 변동사항이 발생했을 때 시그널(사용자 정의 시그널)을 각 변수에 저장
    _domain1_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain2_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain3_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain4_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain5_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain6_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain7_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain8_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain9_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain10_change_detected_tableWidget_signal = pyqtSignal(dict)
    _domain11_change_detected_tableWidget_signal = pyqtSignal(dict)
    update_statusBar_signal = pyqtSignal(str)
    
    def __init__(self, session):
        super().__init__()
        self.__session = session
        # MAIN_PAGE_URL : 변경사항을 탐지 하기 위한 홈페이지 주소들
        self.MAIN_PAGE_URL = {
            "domain1": ["https://domain1.com/index.html"],
            "domain2": ["https://domain2.com/index.html",
                      "https://domain2_2.com/index.html",
                      "https://domain2_3.com/index.html",
                      "https://domain2_4.com/index.html"],
            "domain3": ["https://domain3.com/index.html",
                      "https://domain3_2.com/index.html",
                      "https://domain3_3.com/index.html",
                      "https://domain3_4.com/index.html",
                      "https://domain3_5.com/index.html"],
            "domain4": ["https://domain4.com/index.html",
                      "https://domain4_2.com/index.html",
                      "https://domain4_3.com/index.html",
                      "https://domain4_4.com/index.html",
                      "https://domain4_5.com/index.html"],
            "domain5": ["https://domain5.com/index.html"],
            "domain6": ["https://domain6.com/index.html"],
            "domain7": ["https://domain7.com/index.html"],
            "domain8": ["https://domain8.com/index.html"],
            "domain9": ["https://domain9.com/index.html"],
            "domain10": ["https://domain10.com/index.html"],
            "domain11": ["https://domain11.com/index.html"]
        }
        # OFFICIAL_ANNOUNCEMENT_PAGE_URL : 페이지의 공지사항이 있는 창
        self.OFFICIAL_ANNOUNCEMENT_PAGE_URL = {
            "domain1": ["https://domain1.com/board.html"],
            "domain2": ["https://domain2.com/board.html",
                      "https://domain2_2.com/board.html",
                      "https://domain2_3.com/board.html",
                      "https://domain2_4.com/board.html"],
            "domain3": ["https://domain3.com/board.html",
                      "https://domain3_2.com/board.html",
                      "https://domain3_3.com/board.html",
                      "https://domain3_4.com/board.html",
                      "https://domain3_5.com/board.html"],
            "domain4": ["https://domain4.com/board.html", 
                      "https://domain4_2.com/board.html", 
                      "https://domain4_3.com/board.html", 
                      "https://domain4_4.com/board.html", 
                      "https://domain4_5.com/board.html"],
            "domain5": ["https://domain5.com/board.html"],
            "domain6": ["https://domain6.com/board.html"],
            "domain7": ["https://domain7.com/board.html"],
            "domain8": ["https://domain8.com/board.html"],
            "domain9": ["https://domain9.com/board.html"],
            "domain10": ["https://domain10.com/board.html"],
            "domain11": ["https://domain11.com/board.html"]        
        }
        
        # 각 도메인별 URL 주소가 여러개이므로, 리스트 형태로 저장되어 있으므로 이중 for문으로 도메인을 각각 저장
        # for url_list in self.MAIN_PAGE_URL.values() :
        #     for element in url_list :
        #         element
        self.main_page_url_list = [element for url_list in self.MAIN_PAGE_URL.values() for element in url_list]
        # 동일한 원리로 공지사항 페이지도 확인
        self.offical_announcement_page_url_list = [element for url_list in self.OFFICIAL_ANNOUNCEMENT_PAGE_URL.values() for element in url_list]
        
        # 위에서 전처리한 URL/공지사항들을 대상으로 변동사항을 다음 객체 생성
        self.url_change_detector = URLChangeDetector("", "", self.main_page_url_list, self.__session)
        self.offcial_announcement_change_detector_domain1 = OfficialAnnouncementChangeDetector("", "", self.offical_announcement_page_url_list, self.__session)
    
    def __del__(self):
        self.exit()
    
    def run(self):
        while True:
            # 부대 홈페이지에 대한 변동사항 조회(signal 활용)
            url_change_detector_result = self.url_change_detector.detect_url_change()
            if url_change_detector_result:
                self.emit_signal(url_change_detector_result)
            print(f"[+] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 메인 페이지 조회 완료")
            # 공지사항에 대한 변동사항 조회(signal 활용)
            offical_announcement_result = self.offcial_announcement_change_detector_domain1.detect_official_announcement_change()
            if offical_announcement_result:
                self.emit_signal(offical_announcement_result)
            print(f"[+] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 공지사항 조회 완료")
            self.update_statusBar_signal.emit("조회 완료")
            self.sleep(180)
            """
            self.sleep(30)
            """
    # 각 시그널별로 전달되는 변동사항을 dict 형태로 슬롯에 전달
    def emit_signal(self, changed_datas: list):
        for changed_data in changed_datas:
            unit = changed_data.pop("unit")
            # 직할부대는 도메인이 하나
            if unit == "domain1":
                self._domain1_change_detected_tableWidget_signal.emit(changed_data)
            # 사단 예하에 있는 여단까지 확인하기 위해 list로 형성
            elif unit in ["domain2", "domain2_2", "domain2_3", "domain2_4"]:
                self._domain2_change_detected_tableWidget_signal.emit(changed_data)
            elif unit in ["domain3", "domain3_2", "domain3_3", "domain3_4", "domain3_5"]:
                self._domain3_change_detected_tableWidget_signal.emit(changed_data)
            elif unit in ["domain4", "domain4_2", "domain4_3", "domain4_4", "domain4_5"]:
                self._domain4_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain5":
                self._domain5_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain6":
                self._domain6_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain7":
                self._domain7_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain8":
                self._domain8_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain9":
                self._domain9_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain10":
                self._domain10_change_detected_tableWidget_signal.emit(changed_data)
            elif unit == "domain11":
                self._domain11_change_detected_tableWidget_signal.emit(changed_data)
    
    def sleep(self, seconds):
        QTest.qWait(seconds * 1000)

# 메인 윈도우 UI를 기반으로 프로그램 메인 생성
class WindowClass(QMainWindow, main_window_class):
    def __init__(self, session):
        super().__init__()
        self.__session = session
        
        self._domain1_contents_dict = {}
        self._domain2_contents_dict = {}
        self._domain3_contents_dict = {}
        self._domain4_contents_dict = {}
        self._domain5_contents_dict = {}
        self._domain6_contents_dict = {}
        self._domain7_contents_dict = {}
        self._domain8_contents_dict = {}
        self._domain9_contents_dict = {}
        self._domain10_contents_dict = {}
        self._domain11_contents_dict = {}
        # 프로그램 메인 UI 세팅
        self.setupUi(self)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.statusBar()
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        # 부대별 변동 사항 및 함수 연결
        self._domain1_change_detected_tableWidget.setColumnWidth(0, 365)
        self._domain1_change_detected_tableWidget.setColumnWidth(1, 115)
        self._domain1_change_detected_tableWidget.setColumnWidth(2, 710)
        self._domain1_change_detected_tableWidget.doubleClicked.connect(self.open_domain1_post_widget)
        self._domain2_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain2_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain2_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain2_change_detected_tableWidget.doubleClicked.connect(self.open_domain2_post_widget)
        self._domain3_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain3_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain3_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain3_change_detected_tableWidget.doubleClicked.connect(self.open_domain3_post_widget)
        self._domain4_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain4_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain4_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain4_change_detected_tableWidget.doubleClicked.connect(self.open_domain4_post_widget)
        self._domain5_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain5_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain5_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain5_change_detected_tableWidget.doubleClicked.connect(self.open_domain5_post_widget)
        self._domain6_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain6_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain6_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain6_change_detected_tableWidget.doubleClicked.connect(self.open_domain6_post_widget)
        self._domain7_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain7_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain7_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain7_change_detected_tableWidget.doubleClicked.connect(self.open_domain7_post_widget)
        self._domain8_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain8_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain8_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain8_change_detected_tableWidget.doubleClicked.connect(self.open_domain8_post_widget)
        self._domain9_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain9_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain9_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain9_change_detected_tableWidget.doubleClicked.connect(self.open_domain9_post_widget)
        self._domain10_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain10_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain10_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain10_change_detected_tableWidget.doubleClicked.connect(self.open_domain10_post_widget)
        self._domain11_change_detected_tableWidget.setColumnWidth(0, 220)
        self._domain11_change_detected_tableWidget.setColumnWidth(1, 114)
        self._domain11_change_detected_tableWidget.setColumnWidth(2, 230)
        self._domain11_change_detected_tableWidget.doubleClicked.connect(self.open_domain11_post_widget)
        
        # 세부사항 표기
        self.post_class = PostClass()
        self.post_class.post_information_tableWidget.setColumnWidth(0, 660)
        self.post_class.post_information_tableWidget.setColumnWidth(1, 660)
        self.post_class.post_information_tableWidget.setColumnWidth(2, 660)
        self.post_class.post_information_tableWidget.setColumnWidth(3, 660)
        self.post_class.post_information_tableWidget.setRowHeight(3, 90)
        
        # 각 부대별로 조회하는 Worker 쓰레드와 부대별 변동 사항
        self.worker = Worker(self.__session)
        self.worker._domain1_change_detected_tableWidget_signal.connect(self._domain1_change_detected_tableWidget_slot)
        self.worker._domain2_change_detected_tableWidget_signal.connect(self._domain2_change_detected_tableWidget_slot)
        self.worker._domain3_change_detected_tableWidget_signal.connect(self._domain3_change_detected_tableWidget_slot)
        self.worker._domain4_change_detected_tableWidget_signal.connect(self._domain4_change_detected_tableWidget_slot)
        self.worker._domain5_change_detected_tableWidget_signal.connect(self._domain5_change_detected_tableWidget_slot)
        self.worker._domain6_change_detected_tableWidget_signal.connect(self._domain6_change_detected_tableWidget_slot)
        self.worker._domain7_change_detected_tableWidget_signal.connect(self._domain7_change_detected_tableWidget_slot)
        self.worker._domain8_change_detected_tableWidget_signal.connect(self._domain8_change_detected_tableWidget_slot)
        self.worker._domain9_change_detected_tableWidget_signal.connect(self._domain9_change_detected_tableWidget_slot)
        self.worker._domain10_change_detected_tableWidget_signal.connect(self._domain10_change_detected_tableWidget_slot)
        self.worker._domain11_change_detected_tableWidget_signal.connect(self._domain11_change_detected_tableWidget_slot)
        self.worker.update_statusBar_signal.connect(self.update_statusBar_slot)
        self.worker.start()
    
    def set_tableWidgetItem_text(self, tablWidget: QTableWidget, row: int, text_list: list) -> None:
        for column in range(3):
            tablWidget.setItem(row, column, QTableWidgetItem(str(text_list[column])))
            
    def set_tableWidgetItem_color(self, tablWidget: QTableWidget, row: int, color: str) -> None:
        for column in range(3):
            tablWidget.item(row, column).setBackground(QColor(color))
    
    # 도메인1 셀 더블 클릭 시
    def open_domain1_post_widget(self):
        row = self._domain1_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain1_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain1_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인2 셀 더블 클릭 시    
    def open_domain2_post_widget(self):
        row = self._domain2_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain2_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain2_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
        
    # 도메인3 셀 더블 클릭 시
    def open_domain3_post_widget(self):
        row = self._domain3_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain3_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain3_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인4 셀 더블 클릭 시
    def open_domain4_post_widget(self):
        row = self._domain4_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain4_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain4_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
        
    # 도메인5 셀 더블 클릭 시
    def open_domain5_post_widget(self):
        row = self._domain5_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain5_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain5_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인6 셀 더블 클릭 시
    def open_domain6_post_widget(self):
        row = self._domain6_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain6_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain6_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인7 셀 더블 클릭 시
    def open_domain7_post_widget(self):
        row = self._domain7_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain7_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain7_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인8 셀 더블 클릭 시
    def open_domain8_post_widget(self):
        row = self._domain8_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain8_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain8_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인9 셀 더블 클릭 시
    def open_domain9_post_widget(self):
        row = self._domain9_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain9_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain9_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인10 셀 더블 클릭 시
    def open_domain10_post_widget(self):
        row = self._domain10_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain10_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain10_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 도메인11 셀 더블 클릭 시
    def open_domain11_post_widget(self):
        row = self._domain11_change_detected_tableWidget.currentIndex().row()
        post_title = self._domain11_change_detected_tableWidget.item(row, 0).text()
        post_contents = self._domain11_contents_dict.get(post_title)
        if post_contents:
            self.post_class.set_window_title(post_title)
            self.post_class.set_post(post_contents)
            self.post_class.show()
            self.post_class.activateWindow()
    
    # 닫기 버튼 클릭 시
    def closeEvent(self, event):
        del self.worker
        del self.post_class
    
    # 도메인1의 변경 사항 존재 시
    # 각 변동 사항을 pyqtSig로 정의한 변수(시그널)에 저장한 다음, emit을 이용해 값 전달, connect를 이용해 slot와 signal 연결
    @pyqtSlot(dict)
    def _domain1_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain1_contents_dict[data.get("title")] = data.get("contents")
        self._domain1_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain1_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain1_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인2의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain2_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain2_contents_dict[data.get("title")] = data.get("contents")
        self._domain2_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain2_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain2_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인3의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain3_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain3_contents_dict[data.get("title")] = data.get("contents")
        self._domain3_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain3_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain3_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인4의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain4_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain4_contents_dict[data.get("title")] = data.get("contents")
        self._domain4_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain4_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain4_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인5의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain5_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain5_contents_dict[data.get("title")] = data.get("contents")
        self._domain5_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain5_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain5_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인6의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain6_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain6_contents_dict[data.get("title")] = data.get("contents")
        self._domain6_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain6_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain6_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인7의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain7_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain7_contents_dict[data.get("title")] = data.get("contents")
        self._domain7_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain7_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain7_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인8의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain8_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain8_contents_dict[data.get("title")] = data.get("contents")
        self._domain8_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain8_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain8_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인9의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain9_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain9_contents_dict[data.get("title")] = data.get("contents")
        self._domain9_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain9_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain9_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인10의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain10_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain10_contents_dict[data.get("title")] = data.get("contents")
        self._domain10_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain10_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain10_change_detected_tableWidget, 0, "#FF7FB5")
    
    # 도메인11의 변경 사항 존재 시
    @pyqtSlot(dict)
    def _domain11_change_detected_tableWidget_slot(self, data: dict) -> None:
        if data.get("contents"):
            self._domain11_contents_dict[data.get("title")] = data.get("contents")
        self._domain11_change_detected_tableWidget.insertRow(0)
        _type = data.get("type")
        if _type == "post_append":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, [data.get("title"), "게시물 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "post_delete":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, [data.get("title"), "게시물 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "attachment_append":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 추가", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "attachment_delete":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, [data.get("title"), "첨부파일 URL 삭제", data.get("attachment")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#FF7FB5")
        elif _type == "url_append":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, ["메인 페이지", "URL 추가", data.get("url")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#72FA80")
        elif _type == "url_delete":
            self.set_tableWidgetItem_text(self._domain11_change_detected_tableWidget, 0, ["메인 페이지", "URL 삭제", data.get("url")])
            self.set_tableWidgetItem_color(self._domain11_change_detected_tableWidget, 0, "#FF7FB5")
   
    # 상태바 업데이트
    @pyqtSlot(str)
    def update_statusBar_slot(self, message):
        self.statusBar().showMessage(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - {message}")

# 변동사항을 표시해주는 위젯
class PostClass(QWidget, post_widget_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        """
        if not os.path.isdir("caches\\"):
            os.mkdir("caches\\")
        else:
            shutil.rmtree("caches\\")
        post_content_page = self.post_contents_webEngineView.page()
        post_content_profile = post_content_page.profile()
        post_content_profile.setCachePath("caches\\")
        """
    
    def __del__(self):
        """
        shutil.rmtree("caches\\")
        """
        pass
    
    # 윈도우 타이틀 설정
    def set_window_title(self, title):
        self.setWindowTitle(title)
    
    # 게시물 내용 적용
    def set_post(self, contents: dict):
        self.post_information_tableWidget.setItem(0, 0, QTableWidgetItem(str(contents.get("title"))))
        self.post_information_tableWidget.setItem(1, 0, QTableWidgetItem(str(contents.get("time"))))
        self.post_information_tableWidget.setItem(2, 0, QTableWidgetItem(str(contents.get("author"))))
        self.post_information_tableWidget.setItem(3, 0, QTableWidgetItem(str(contents.get("attachemnts"))))
        self.post_contents_webEngineView.setHtml(contents.get("contents"))
    
    # 닫기 버튼 클릭 시
    def closeEvent(self, event):
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginClass()
    login_window.show()
    if app.exec_() == 1:
        session = login_window.get_session()
        main_window = WindowClass(session)
        main_window.showMaximized()
        del login_window
        app.exec_()