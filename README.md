# 홈페이지 변조 추적관리
## 1. 개요
- 군단 예하부대들의 홈페이지 변경 사항들을 추적 관리
- 첨부파일 링크 변경, 신규 게시글 탑재 등 변동사항을 표시
- PyQt5를 활용한 GUI 환경에서 관제
- 기준점이 되는 특정 시간의 페이지를 먼저 스크래핑한후 주기적인 시간 간격을 두고 해당 페이지를 다시 요청하여 변동사항을 체크하는 방식
## 2. 스택
- Python

## 3. 제작 동기
- 사이버 훈련 간에, 군단에서는 WAF를 운용하지 않기 때문에 홈페이지를 대상으로 한 공격에 대해서는 탐지가 불가능
- 서버 자체는 데이터센터에 있기 때문에 책임의 소지에서는 다소 자유로우나, 변조된 게시글 클릭시 사용자가 감염되는 상황 발생

## 4. 역할
- 양진수 : 기획
- 김동언 : 코딩

## 5. 배운 것
- 너무 많은 조회를 다양하게 실행하면 서버에서 봇으로 인식할 수 있으므로 그 부분을 회피하기 위해 일부 시간 간격을 두었음
- 파이썬 크롤링을 공부하면서 사용했던 라이브러리를 적극적으로 활용할 수 있었음

## 6. 아쉬운 점
- 크롤링을 하는 것 자체로 서버에 부담을 주게되므로 서버에 부담을 주지 않으면서 관제 작전의 효과를 증대시키기 위한 시간을 판단할만한 데이터가 없어서 경험과 시행착오에 의존해야했음
- 각 게시판에 연결되어 있는 url이나 자원들의 변조 여부는 확인할 수 있으나 최초에 변조된 첨부파일이 탑재되는 경우 탐지 불가
- 웹스크래핑 기반으로 동작하며 자칫하면 서버에 부담을 줄 수 있음 
- 비동기 처리 방식이 아닌 동기 처리 방식으로 동작하여 속도의 한계 존재함
- 다수의 첨부 파일의 해시값을 검사하여 첨부 파일 자체의 변경 또한 검사하려 했지만, 이 또한 동기 처리 방식으로 인한 동작 속도 저하로 추가하지 못함

## 7. 실행 방법
- 압축 해제 후, main.pyw 실행

## 8. 프로그램 화면
- 민감 정보는 전부 검은색으로 마스킹처리했습니다.
- ![image](https://github.com/fjybjinsu/HomepageEdit/assets/85774577/5b9839a5-65cb-4ac6-bf2c-a8f2a59b3317)
