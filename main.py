# 메인 실행 파일

import os
from config import GA_PROPERTY_ID, GA_CREDENTIALS_FILE, NOTION_TOKEN, NOTION_PARENT_PAGE_ID
from ga_client import GoogleAnalyticsClient
from notion_client import NotionClient


def main():
    """
    구글 애널리틱스 데이터를 노션 페이지에 보고하는 메인 함수
    """
    
    
    try:
        # 구글 애널리틱스 클라이언트 초기화
        ga_client = GoogleAnalyticsClient(
            property_id=GA_PROPERTY_ID,
            credentials_file=GA_CREDENTIALS_FILE
        )
        
        # 노션 클라이언트 초기화
        notion_client = NotionClient(
            token=NOTION_TOKEN,
            parent_page_id=NOTION_PARENT_PAGE_ID
        )
        
        # 구글 애널리틱스 데이터 가져오기
        ga_data = ga_client.get_yesterday_data()
        
        # 노션 페이지 생성
        result = notion_client.create_ga_report_page(ga_data)
        
        if result:
            print("데일리 리포트가 성공적으로 생성되었습니다.")
            print(f"날짜: {ga_data['date']}")
            print(f"활성 사용자: {ga_data['active_users']}명")
        else:
            print("데일리 리포트 생성 실패")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()