import sys
import unittest
from io import BytesIO
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import app
from lexer import Lexer


class FetchSupportTests(unittest.TestCase):
    def test_fetch_tokenizes_without_trailing_semicolon(self):
        script = 'FETCH Podcast_Name WHERE Episode_Length_Minutes >70 AND Publication_Day = "Sunday"'
        self.assertEqual(
            Lexer(script).tokenize(),
            [('FETCH', 'FETCH Podcast_Name WHERE Episode_Length_Minutes >70 AND Publication_Day = "Sunday";')],
        )

    def test_fetch_returns_filtered_preview(self):
        client = app.test_client()
        csv_bytes = (
            b"Podcast_Name,Episode_Length_Minutes,Publication_Day\n"
            b"Show A,80,Sunday\n"
            b"Show B,55,Sunday\n"
            b"Show C,90,Monday\n"
            b"Show D,75,Sunday\n"
        )

        response = client.post(
            "/run-script",
            data={
                "file": (BytesIO(csv_bytes), "podcasts.csv"),
                "script": 'FETCH Podcast_Name WHERE Episode_Length_Minutes >70 AND Publication_Day = "Sunday"',
            },
            content_type="multipart/form-data",
        )

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(payload["filename"])
        self.assertEqual(
            payload["preview"],
            [{"Podcast_Name": "Show A"}, {"Podcast_Name": "Show D"}],
        )
        self.assertEqual(payload["result"]["type"], "table")

    def test_fetch_matches_columns_with_spaces(self):
        client = app.test_client()
        csv_bytes = (
            b"Podcast Name,Episode Length Minutes,Publication Day\n"
            b"Show A,80,Sunday\n"
            b"Show B,55,Sunday\n"
            b"Show C,90,Monday\n"
            b"Show D,75,Sunday\n"
        )

        response = client.post(
            "/run-script",
            data={
                "file": (BytesIO(csv_bytes), "podcasts.csv"),
                "script": 'FETCH Podcast_Name WHERE Episode_Length_Minutes >70 AND Publication_Day = "Sunday"',
            },
            content_type="multipart/form-data",
        )

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload["preview"],
            [{"Podcast_Name": "Show A"}, {"Podcast_Name": "Show D"}],
        )


if __name__ == "__main__":
    unittest.main()
