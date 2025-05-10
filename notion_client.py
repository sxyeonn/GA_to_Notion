# notion_client.py
# 노션 API와 통신하는 모듈

import requests
import datetime
from typing import Dict, Any, List, Optional

class NotionClient:
    def __init__(self, token: str, parent_page_id: str):
        """
        노션 API 클라이언트 초기화
        
        Args:
            token (str): 노션 API 토큰
            parent_page_id (str): 부모 페이지 ID
        """
        self.token = token
        self.parent_page_id = parent_page_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def create_ga_report_page(self, ga_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        GA 데이터를 포함한 노션 페이지를 생성합니다.
        
        Args:
            ga_data (dict): 구글 애널리틱스 데이터
            
        Returns:
            dict or None: 성공 시 응답 데이터, 실패 시 None
        """
        # 페이지 제목 설정
        date_obj = datetime.datetime.strptime(ga_data['date'], '%Y-%m-%d')
        formatted_date = date_obj.strftime('%Y년 %m월 %d일')
        page_title = f"Yeonny's BLOG {formatted_date} 리포트"
        
        # 노션 페이지 콘텐츠 구성
        children = self._build_page_content(ga_data)
        
        # 트래픽 소스 섹션 추가
        traffic_source_blocks = self._build_traffic_source_section(ga_data)
        children.extend(traffic_source_blocks)
        
        # 인기 페이지 섹션 추가
        popular_pages_blocks = self._build_popular_pages_section(ga_data)
        children.extend(popular_pages_blocks)
        
        # 노션 API 요청 데이터
        data = {
            "parent": {
                "page_id": self.parent_page_id
            },
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                }
            },
            "icon": {
            "type": "emoji",
            "emoji": "📊"
            },
            "children": children
        }
        
        # 노션 API 호출하여 페이지 생성
        response = requests.post('https://api.notion.com/v1/pages', headers=self.headers, json=data)
        
        if response.status_code == 200:
            print(f"성공적으로 노션 페이지를 생성했습니다: {page_title}")
            return response.json()
        else:
            print(f"노션 페이지 생성 실패: {response.status_code}")
            print(f"에러 메시지: {response.text}")
            return None
    
    def _build_page_content(self, ga_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        노션 페이지의 핵심 지표 섹션을 구성합니다.
        
        Args:
            ga_data (dict): 구글 애널리틱스 데이터
            
        Returns:
            list: 노션 블록 객체 목록
        """
        # 전일 대비 변화 계산 및 이모지 추가
        active_users_change = ga_data['active_users'] - ga_data['prev_active_users']
        active_users_emoji = "📈" if active_users_change >= 0 else "📉"
        
        page_views_change = ga_data['page_views'] - ga_data['prev_page_views']
        page_views_emoji = "📈" if page_views_change >= 0 else "📉"
        
        # 참여율 변화
        engagement_rate_change = ga_data['engagement_rate'] - ga_data['prev_engagement_rate']
        engagement_emoji = "📈" if engagement_rate_change >= 0 else "📉"
        
        # 세션 변화
        sessions_change = ga_data['sessions'] - ga_data['prev_sessions']
        sessions_emoji = "📈" if sessions_change >= 0 else "📉"
        
        # 평균 세션 지속 시간 변화
        avg_session_duration_change = ga_data.get('avg_session_duration', 0) - ga_data.get('prev_avg_session_duration', 0)
        duration_emoji = "📈" if avg_session_duration_change >= 0 else "📉"
        
        # 이탈률 변화 (이탈률은 낮을수록 좋음)
        bounce_rate_change = ga_data.get('bounce_rate', 0) - ga_data.get('prev_bounce_rate', 0)
        bounce_emoji = "📉" if bounce_rate_change >= 0 else "📈"  # 이탈률은 낮을수록 좋음
        
        # 시간 포맷팅 함수
        def format_duration(seconds):
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}분 {remaining_seconds}초"
        
        children = [
            # 빈 줄
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 오늘의 핵심 지표 섹션 헤더
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "[ 오늘의 핵심 지표 ]"
                            }
                        }
                    ]
                }
            },
            # 방문자 정보
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "방문자: "
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"{ga_data['active_users']}명 "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"(전일대비 {'+' if active_users_change >= 0 else ''}{active_users_change}명) {active_users_emoji}"
                            }
                        }
                    ]
                }
            },
            # 페이지 조회 정보
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "페이지 조회: "
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"{ga_data['page_views']}회 "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"(전일대비 {'+' if page_views_change >= 0 else ''}{page_views_change}회) {page_views_emoji}"
                            }
                        }
                    ]
                }
            },
            # 세션 수 정보
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "세션 수: "
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"{ga_data['sessions']}회 "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"(전일대비 {'+' if sessions_change >= 0 else ''}{sessions_change}회) {sessions_emoji}"
                            }
                        }
                    ]
                }
            }
        ]
        
        # 평균 체류 시간 정보 (데이터가 있는 경우에만)
        if 'avg_session_duration' in ga_data:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "평균 체류 시간: "
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"{format_duration(ga_data['avg_session_duration'])} "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"(전일대비 {'+' if avg_session_duration_change >= 0 else '-'}{format_duration(abs(avg_session_duration_change))}) {duration_emoji}"
                            }
                        }
                    ]
                }
            })
        
        # 참여율 정보
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "참여율: "
                        },
                        "annotations": {
                            "bold": True
                        }
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": f"{ga_data['engagement_rate']:.2f}% "
                        }
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": f"(전일대비 {'+' if engagement_rate_change >= 0 else ''}{engagement_rate_change:.2f}%p) {engagement_emoji}"
                        }
                    }
                ]
            }
        })
        
        # 이탈률 정보 (데이터가 있는 경우에만)
        if 'bounce_rate' in ga_data:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "이탈률: "
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"{ga_data['bounce_rate']:.2f}% "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f"(전일대비 {'+' if bounce_rate_change >= 0 else ''}{abs(bounce_rate_change):.2f}%p) {bounce_emoji}"
                            }
                        }
                    ]
                }
            })
        
        # 빈 줄 추가
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": []
            }
        })
        
        return children
    
    def _build_traffic_source_section(self, ga_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        트래픽 소스 섹션을 구성합니다.
        
        Args:
            ga_data (dict): 구글 애널리틱스 데이터
            
        Returns:
            list: 노션 블록 객체 목록
        """
        blocks = [
            # 트래픽 소스 섹션 헤더
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "[ 트래픽 소스 ]"
                            }
                        }
                    ]
                }
            }
        ]
        
        # 총 세션 수 계산
        total_sessions = ga_data['sessions']
        
        # 트래픽 소스 목록 추가 (글머리 기호 목록 형식으로)
        for source in ga_data['sources']:
            source_name = source['source']
            sessions = source['sessions']
            percentage = (sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"{source_name}:"
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f" {sessions}회 ({percentage:.1f}%)"
                            }
                        }
                    ]
                }
            })
        
        # 빈 줄 추가
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": []
            }
        })
        
        return blocks
    
    def _build_popular_pages_section(self, ga_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        인기 페이지 섹션을 구성합니다.
        
        Args:
            ga_data (dict): 구글 애널리틱스 데이터
            
        Returns:
            list: 노션 블록 객체 목록
        """
        blocks = [
            # 인기 페이지 섹션 헤더
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "[ 조회수 Top 5 ]"
                            }
                        }
                    ]
                }
            }
        ]
        
        # 인기 페이지 목록 추가
        for i, page in enumerate(ga_data['popular_pages']):
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"{page['views']}회 |"
                            },
                            "annotations": {
                                "bold": True
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f" {page['title']}"
                            }
                        }
                    ]
                }
            })
        
        # 빈 줄 추가
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": []
            }
        })
        
        return blocks

    def test_token(self) -> bool:
        """
        노션 API 토큰이 유효한지 테스트합니다.
        
        Returns:
            bool: 토큰이 유효하면 True, 그렇지 않으면 False
        """
        try:
            # 간단한 API 호출로 토큰 유효성 검사
            response = requests.get(
                'https://api.notion.com/v1/users/me',
                headers=self.headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"토큰 유효성 확인 성공! 사용자: {user_data.get('name', '이름 없음')}")
                return True
            else:
                print(f"토큰 유효성 확인 실패: {response.status_code}")
                print(f"에러 메시지: {response.text}")
                return False
        except Exception as e:
            print(f"토큰 테스트 중 오류 발생: {str(e)}")
            return False
    
    