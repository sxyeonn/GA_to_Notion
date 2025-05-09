# ga_client.py
# 구글 애널리틱스 API와 통신하는 모듈

import os
import datetime
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension, OrderBy, Filter, FilterExpression

class GoogleAnalyticsClient:
    def __init__(self, property_id, credentials_file=None):
        """
        구글 애널리틱스 API 클라이언트 초기화
        
        Args:
            property_id (str): 구글 애널리틱스 속성 ID
            credentials_file (str, optional): 서비스 계정 키 파일 경로
        """
        self.property_id = property_id
        
        # 자격증명 파일 설정
        if credentials_file:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
        
        # GA 클라이언트 초기화
        self.client = BetaAnalyticsDataClient()
    
    def get_yesterday_data(self):
        """
        어제 날짜의 주요 GA 데이터와 이전 날짜 데이터를 함께 가져옵니다.
        
        Returns:
            dict: 어제와 이전 날짜의 GA 데이터를 포함한 딕셔너리
        """
        # 날짜 계산
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        day_before_yesterday = today - datetime.timedelta(days=2)
        
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        day_before_yesterday_str = day_before_yesterday.strftime('%Y-%m-%d')
        
        # 1. 어제의 기본 지표 가져오기
        yesterday_metrics = self._get_metrics(yesterday_str)
        
        # 2. 이전 날짜의 기본 지표 가져오기 (비교용)
        day_before_metrics = self._get_metrics(day_before_yesterday_str)
        
        # 3. 어제의 트래픽 소스 가져오기
        sources_response = self._get_traffic_sources(yesterday_str)
        
        # 4. 어제의 인기 페이지 가져오기
        pages_response = self._get_popular_pages(yesterday_str)
        
        # 5. 어제의 평균 세션 지속 시간 및 이탈률 가져오기
        engagement_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=yesterday_str, end_date=yesterday_str)],
            metrics=[
                Metric(name='averageSessionDuration'),
                Metric(name='bounceRate')
            ]
        )
        
        engagement_response = self.client.run_report(engagement_request)
        
        # 6. 이전 날짜의 평균 세션 지속 시간 및 이탈률 가져오기
        prev_engagement_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=day_before_yesterday_str, end_date=day_before_yesterday_str)],
            metrics=[
                Metric(name='averageSessionDuration'),
                Metric(name='bounceRate')
            ]
        )
        
        prev_engagement_response = self.client.run_report(prev_engagement_request)
        
        # 결과 데이터 정리
        result = {
            'date': yesterday_str,
            'active_users': int(yesterday_metrics.rows[0].metric_values[0].value) if yesterday_metrics.rows else 0,
            'prev_active_users': int(day_before_metrics.rows[0].metric_values[0].value) if day_before_metrics.rows else 0,
            'page_views': int(yesterday_metrics.rows[0].metric_values[1].value) if yesterday_metrics.rows else 0,
            'prev_page_views': int(day_before_metrics.rows[0].metric_values[1].value) if day_before_metrics.rows else 0,
            'sessions': int(yesterday_metrics.rows[0].metric_values[2].value) if yesterday_metrics.rows else 0,
            'prev_sessions': int(day_before_metrics.rows[0].metric_values[2].value) if day_before_metrics.rows else 0,
            'engagement_rate': float(yesterday_metrics.rows[0].metric_values[3].value) * 100 if yesterday_metrics.rows else 0,
            'prev_engagement_rate': float(day_before_metrics.rows[0].metric_values[3].value) * 100 if day_before_metrics.rows else 0,
            'sources': [],
            'popular_pages': []
        }
        
        # 평균 세션 지속 시간 및 이탈률 추가
        if engagement_response.rows:
            result['avg_session_duration'] = float(engagement_response.rows[0].metric_values[0].value)
            result['bounce_rate'] = float(engagement_response.rows[0].metric_values[1].value)
        else:
            result['avg_session_duration'] = 0
            result['bounce_rate'] = 0
            
        if prev_engagement_response.rows:
            result['prev_avg_session_duration'] = float(prev_engagement_response.rows[0].metric_values[0].value)
            result['prev_bounce_rate'] = float(prev_engagement_response.rows[0].metric_values[1].value)
        else:
            result['prev_avg_session_duration'] = 0
            result['prev_bounce_rate'] = 0
        
        # 트래픽 소스 데이터 정리
        for row in sources_response.rows:
            source = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            result['sources'].append({
                'source': source,
                'sessions': sessions
            })
        
        # 인기 페이지 데이터 정리
        for row in pages_response.rows:
            page_title = row.dimension_values[0].value
            views = int(row.metric_values[0].value)
            result['popular_pages'].append({
                'title': page_title,
                'views': views
            })
        
        return result
    
    def _get_metrics(self, date):
        """
        기본 지표 데이터를 가져옵니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='screenPageViews'),
                Metric(name='sessions'),
                Metric(name='engagementRate')
            ]
        )
        
        return self.client.run_report(request)
    
    def _get_traffic_sources(self, date):
        """
        트래픽 소스 데이터를 가져옵니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='sessionSource')],
            metrics=[Metric(name='sessions')],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
            ],
            limit=5  # 상위 5개만 가져옴
        )
        
        return self.client.run_report(request)
    
    def _get_popular_pages(self, date):
        """
        인기 페이지 데이터를 가져옵니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='pageTitle')],
            metrics=[Metric(name='screenPageViews')],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
            ],
            limit=5  # 상위 5개만 가져옴
        )
        
        return self.client.run_report(request)
        
    def get_device_stats(self, date):
        """
        디바이스 카테고리별 사용자 통계를 가져옵니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='deviceCategory')],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='sessions'),
                Metric(name='engagementRate')
            ]
        )
        
        return self.client.run_report(request)
    
    def get_content_performance(self, date, limit=10):
        """
        개별 블로그 포스트 성과를 분석합니다.
        인기 있는 포스트, 체류 시간이 긴 포스트 등을 파악할 수 있습니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='pageTitle'), Dimension(name='pagePath')],
            metrics=[
                Metric(name='screenPageViews'),
                Metric(name='userEngagementDuration'),
                Metric(name='engagementRate')
            ],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
            ],
            limit=limit
        )
        
        return self.client.run_report(request)
    
    def get_content_engagement(self, date, limit=10):
        """
        콘텐츠별 체류 시간을 분석합니다.
        어떤 글이 사용자의 관심을 가장 오래 끌었는지 파악할 수 있습니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='pageTitle')],
            metrics=[
                Metric(name='userEngagementDuration'),
                Metric(name='screenPageViews'),
                Metric(name='engagementRate')
            ],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="userEngagementDuration"), desc=True)
            ],
            limit=limit
        )
        
        return self.client.run_report(request)
    
    def get_detailed_traffic_sources(self, date):
        """
        블로그 트래픽이 어디서 오는지 상세하게 분석합니다.
        검색 엔진, 소셜 미디어, 직접 방문 등의 비율을 파악할 수 있습니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[
                Dimension(name='sessionDefaultChannelGroup'),
                Dimension(name='sessionSource'),
                Dimension(name='sessionMedium')
            ],
            metrics=[
                Metric(name='sessions'),
                Metric(name='activeUsers'),
                Metric(name='engagementRate')
            ],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
            ]
        )
        
        return self.client.run_report(request)
    
    def get_new_vs_returning(self, date):
        """
        신규 방문자와 재방문자 비율을 분석합니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='newVsReturningUser')],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='sessions'),
                Metric(name='engagementRate'),
                Metric(name='screenPageViewsPerSession')
            ]
        )
        
        return self.client.run_report(request)
    
    def get_time_patterns(self, start_date, end_date):
        """
        시간대별, 요일별 트래픽 패턴을 분석합니다.
        언제 블로그 방문이 가장 많은지 파악할 수 있습니다.
        """
        # 시간대별 트래픽
        hourly_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name='hour')],
            metrics=[Metric(name='activeUsers')],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))]
        )
        
        # 요일별 트래픽
        daily_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name='dayOfWeek')],
            metrics=[Metric(name='activeUsers')],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="dayOfWeek"))]
        )
        
        return {
            'hourly': self.client.run_report(hourly_request),
            'daily': self.client.run_report(daily_request)
        }
    
    def get_geographic_data(self, date):
        """
        지역별 블로그 사용자를 분석합니다.
        국가 및 도시별 방문자 현황을 파악할 수 있습니다.
        """
        # 국가별 분석
        country_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='country')],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='sessions'),
                Metric(name='engagementRate')
            ],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)
            ],
            limit=10
        )
        
        # 도시별 분석 (한국으로 제한)
        city_request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='city')],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='sessions')
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="country",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="South Korea"
                    )
                )
            ),
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)
            ],
            limit=10
        )
        
        return {
            'country': self.client.run_report(country_request),
            'city': self.client.run_report(city_request)
        }
    
    def get_weekly_trend(self, end_date, days=7):
        """
        주간 트렌드를 가져옵니다.
        최근 7일간의 핵심 지표 트렌드를 분석합니다.
        """
        # 날짜 계산
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date_obj = end_date_obj - datetime.timedelta(days=days-1)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name='date')],
            metrics=[
                Metric(name='activeUsers'),
                Metric(name='screenPageViews'),
                Metric(name='sessions'),
                Metric(name='engagementRate')
            ],
            order_bys=[
                OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))
            ]
        )
        
        return self.client.run_report(request)
    
    def get_category_performance(self, date):
        """
        블로그 카테고리별 성과를 분석합니다.
        티스토리 URL 패턴(/category/카테고리명)을 기반으로 합니다.
        """
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            date_ranges=[DateRange(start_date=date, end_date=date)],
            dimensions=[Dimension(name='pagePath')],
            metrics=[
                Metric(name='screenPageViews'),
                Metric(name='activeUsers'),
                Metric(name='engagementRate')
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="pagePath",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.CONTAINS,
                        value="/category/"
                    )
                )
            )
        )
        
        return self.client.run_report(request)