#!/bin/bash

# 사용법
# 기본: ./seokjin_deposit.sh
# 일자지정: ./seokjin_deposit.sh 7 -> 7일전 ~ 오늘

# 같은 폴더에 있는 .env 파일에서 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "에러: .env 파일을 찾을 수 없습니다."
    exit 1
fi

# 첫 번째 인자($1)가 있으면 그 값을 사용하고, 없으면 디폴트 3 사용
DAYS=${1:-3}

# 'N일치' 조회를 위해 date 명령어에 넣을 일수 계산 (오늘을 포함하므로 DAYS - 1 일 전을 구함)
SUB_DAYS=$((DAYS - 1))

# OS 감지 후 날짜 계산
if [[ "$OSTYPE" == "darwin"* ]]; then
    START_DATE=$(date -v-${SUB_DAYS}d +%Y%m%d)
    END_DATE=$(date +%Y%m%d)
else
    START_DATE=$(date -d "${SUB_DAYS} days ago" +%Y%m%d)
    END_DATE=$(date +%Y%m%d)
fi

echo "조회 기간 (${DAYS}일치): $START_DATE ~ $END_DATE"

# 가상환경 동기화 (이미 되어있으면 uv가 알아서 초고속 스킵함)
echo "의존성 확인 중..."
uv sync
echo "의존성 확인 완료"

echo "혜미 계좌 입금 내역 확인 중..."
#혜미 계좌 실행
uv run python ./bankapi_to_supabase.py --apikey "$API_KEY" --secretkey "$SECRET_KEY" --accountNumber "69890201368816" --startDate "$START_DATE" --endDate "$END_DATE" --ignoreSslError
