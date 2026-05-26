# bank_account_deposit_batch

BankAPI에서 계좌 거래내역을 조회한 뒤 Supabase `bank_account_deposit` 테이블에 적재하는 배치입니다.

## 의존성 설치

```powershell
uv sync
```

## 환경변수

Supabase 접속 정보는 `.env`에 설정합니다.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

## 실행

```powershell
uv run python .\bankapi_to_supabase.py `
  --apikey "pk_live_xxx" `
  --secretkey "sk_client_xxx" `
  --accountNumber "1234567890"
```

`--startDate`, `--endDate`를 생략하면 둘 다 실행일 기준 오늘 날짜로 호출합니다.
특정 기간을 조회하려면 다음처럼 `YYYYMMDD` 형식으로 넘깁니다.

```powershell
uv run python .\bankapi_to_supabase.py `
  --apikey "pk_live_xxx" `
  --secretkey "sk_client_xxx" `
  --accountNumber "1234567890" `
  --startDate "20260101" `
  --endDate "20260110"
```

SSL 인증서 오류가 발생하면 다음처럼 Supabase와 BankAPI의 인증서 검증을 끄고 실행할 수 있습니다.

```powershell
uv run python .\bankapi_to_supabase.py `
  --apikey "pk_live_xxx" `
  --secretkey "sk_client_xxx" `
  --accountNumber "1234567890" `
  --startDate "20260101" `
  --endDate "20260110" `
  --ignoreSslError
```

`accountNumber`는 Supabase `bank_account.bank_account_number`와 비교합니다.
일치하는 계좌의 `id`, `bank_code`, `account_password`, `resident_number`를 사용해 BankAPI를 호출합니다.

## 적재 규칙

`bank_account_deposit`에는 BankAPI 응답 중 `type`이 `deposit`인 거래만 삽입합니다.
삽입 컬럼은 다음과 같습니다.

- `bank_account_id`
- `date`
- `time`
- `counterparty`
- `amount`

삽입 전 `bank_account_id`, `date`, `time`, `counterparty`, `amount`가 모두 같은 행이 이미 있으면 중복으로 보고 건너뜁니다.



uv run python .\bankapi_to_supabase.py `
  --apikey "pk_live_0169cb871e27e5074d6c8073b3914ce7" `
  --secretkey "sk_client_minimal_eca54aabbc4954cc7c448268fbe3c8d5" `
  --accountNumber "1002950943065" `
  --startDate "20260525" `
  --endDate "20260525" `
  --ignoreSslError

uv run python .\bankapi_to_supabase.py `
  --apikey "pk_live_0169cb871e27e5074d6c8073b3914ce7" `
  --secretkey "sk_client_minimal_eca54aabbc4954cc7c448268fbe3c8d5" `
  --accountNumber "69890201368816" `
  --startDate "20260525" `
  --endDate "20260525" `
  --ignoreSslError
