import argparse
import os
from datetime import datetime

from dotenv import load_dotenv
from httpx import Client as HttpxClient
import requests
from requests.exceptions import HTTPError
from requests.exceptions import SSLError
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions
import urllib3


BANKAPI_TRANSACTIONS_URL = "https://api.bankapi.co.kr/v1/transactions"


def parse_args():
    today = datetime.now().strftime("%Y%m%d")
    parser = argparse.ArgumentParser(
        description="BankAPI 거래내역을 조회해서 Supabase에 적재합니다."
    )
    parser.add_argument("--apikey", required=True)
    parser.add_argument("--secretkey", required=True)
    parser.add_argument("--accountNumber", required=True)
    parser.add_argument("--startDate", default=today)
    parser.add_argument("--endDate", default=today)
    parser.add_argument("--ignoreSslError", action="store_true")
    return parser.parse_args()


def get_supabase_client(ignore_ssl_error):
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_KEY"]

    if ignore_ssl_error:
        httpx_client = HttpxClient(verify=False)
        options = SyncClientOptions(httpx_client=httpx_client)
        return create_client(supabase_url, supabase_key, options)

    return create_client(supabase_url, supabase_key)


def get_bank_account(supabase, account_number):
    response = (
        supabase.table("bank_account")
        .select("id, bank_code, bank_password, resident_number")
        .eq("bank_account_number", account_number)
        .limit(1)
        .execute()
    )
    if not response.data:
        print("account_number: " + account_number)
        raise SystemExit("bank_account 테이블에서 accountNumber와 일치하는 계좌를 찾지 못했습니다.")

    return response.data[0]


def fetch_transactions(args, bank_account):
    if args.ignoreSslError:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        response = requests.post(
            BANKAPI_TRANSACTIONS_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {args.apikey}:{args.secretkey}",
            },
            json={
                "bankCode": bank_account["bank_code"],
                "accountNumber": "{"+args.accountNumber+"}",
                "accountPassword": bank_account["bank_password"],
                "residentNumber": bank_account["resident_number"],
                "startDate": args.startDate,
                "endDate": args.endDate,
            },
            timeout=30,
            verify=not args.ignoreSslError,
        )
    except SSLError as error:
        raise SystemExit(
            "BankAPI SSL 인증서 검증에 실패했습니다. "
            "--ignoreSslError 옵션을 붙여 다시 실행할 수 있습니다. "
            f"원인: {error}"
        ) from error

    try:
        response.raise_for_status()
    except HTTPError as error:
        raise SystemExit(
            "BankAPI HTTP 오류가 발생했습니다. "
            f"status={response.status_code} body={response.text}"
        ) from error

    data = response.json()
    if not data.get("success"):
        raise SystemExit(f"BankAPI 호출이 실패했습니다: {data}")

    return data.get("transactions", [])


def deposit_exists(supabase, row):
    response = (
        supabase.table("bank_account_deposit")
        .select("id")
        .eq("bank_account_id", row["bank_account_id"])
        .eq("date", row["date"])
        .eq("time", row["time"])
        .eq("counterparty", row["counterparty"])
        .eq("amount", row["amount"])
        .limit(1)
        .execute()
    )
    return bool(response.data)


def insert_transactions(supabase, bank_account_id, transactions):
    inserted_count = 0
    skipped_count = 0

    for transaction in transactions:
        if transaction["type"] != "deposit":
            continue

        row = {
            "bank_account_id": bank_account_id,
            "date": transaction["date"],
            "time": transaction["time"],
            "counterparty": transaction["counterparty"],
            "amount": transaction["amount"],
        }

        if deposit_exists(supabase, row):
            skipped_count += 1
            continue

        supabase.table("bank_account_deposit").insert(row).execute()
        inserted_count += 1

    return inserted_count, skipped_count


def main():
    load_dotenv()
    args = parse_args()
    supabase = get_supabase_client(args.ignoreSslError)
    bank_account = get_bank_account(supabase, args.accountNumber)
    transactions = fetch_transactions(args, bank_account)
    inserted_count, skipped_count = insert_transactions(
        supabase, bank_account["id"], transactions
    )

    print(f"inserted={inserted_count} skipped_duplicates={skipped_count}")


if __name__ == "__main__":
    main()
