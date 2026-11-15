import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingest.paths import DATA_ROOT

log = logging.getLogger("ingest.openphish_snapshot")


def fetch_openphish_feed(url: str) -> str:

    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=4,
                backoff_factor=30,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )
        ),
    )

    r = session.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "phishing-domain-monitor (github.com/shawar8/phishing-domain-monitor)"
        },
    )

    r.raise_for_status()

    return r.text


def save_raw_data(text: str, data_folder: Path, day: str, stem: str) -> Path:

    text_output = data_folder / f"date={day}" / f"{stem}.txt"
    text_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.write_text(text, encoding="utf-8")
    return text_output


def process_feed(text: str, run_ts: datetime):
    rows, rejected = [], 0
    seen = set()

    for line in text.splitlines():
        # remove whitespace
        url = line.strip()
        # check if text present after stripping
        if not url:
            continue
        # rejecting if url does not start with http:// or https://
        if not url.lower().startswith(("http://", "https://")):
            rejected += 1
            continue
        # check if url is already seen
        if url in seen:
            continue
        seen.add(url)
        rows.append([run_ts, "openphish", url])

    df = pd.DataFrame(rows, columns=["snapshot_at", "source", "url"])
    return df, rejected


def validate_feed(df: pd.DataFrame, rejected: int):

    n = df.shape[0]
    log.info(f"Total rows: {n}, Rejected rows: {rejected}")
    if n < 50 or rejected > 0.05 * (n + rejected):
        raise RuntimeError(
            f"Too few rows or too many rejected rows: {n} rows, {rejected} rejected"
        )


def save_csv(df: pd.DataFrame, text_output: Path):

    csv_output = text_output.with_suffix(".csv")
    df.to_csv(csv_output, index=False, encoding="utf-8")
    log.info(f"CSV output written to {csv_output}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    data_folder = DATA_ROOT / "raw" / "openphish"
    run_ts = datetime.now(UTC)
    day = run_ts.strftime("%Y-%m-%d")
    stem = f"feed-{run_ts:%H%M%S}Z"

    text = fetch_openphish_feed("https://openphish.com/feed.txt")

    text_output = save_raw_data(text, data_folder, day, stem)
    df, rejected = process_feed(text, run_ts)
    validate_feed(df, rejected)
    save_csv(df, text_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())