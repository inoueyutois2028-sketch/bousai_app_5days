import json
import os
import tempfile
import unittest

import app as app_module


class ShelterRegisterTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = os.path.join(self.temp_dir.name, 'shelters.json')
        with open(self.temp_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

        app_module.DATA_FILE = self.temp_path
        app_module.shelters = []
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

        with self.client.session_transaction() as session:
            session['logged_in'] = True
            session['username'] = 'admin'

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_shelter_persists_data(self):
        response = self.client.post(
            '/shelter_register',
            data={'name': '新しい避難所'},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('新しい避難所', response.get_data(as_text=True))

        with open(self.temp_path, 'r', encoding='utf-8') as f:
            saved = json.load(f)

        self.assertEqual(saved[-1]['name'], '新しい避難所')

        all_results = self.client.get('/all_shelters')
        self.assertEqual(all_results.status_code, 200)
        self.assertIn('新しい避難所', all_results.get_data(as_text=True))

    def test_parse_area_warnings_matches_aomori_city_codes(self):
        warning_data = [{
            'reportDatetime': '2026-09-02T11:17:00+09:00',
            'warning': {
                'class10Items': [{
                    'areaCode': '020010',
                    'kinds': [{'code': '43', 'status': '継続'}]
                }],
                'class20Items': [{
                    'areaCode': '0220100',
                    'kinds': [{'code': '14', 'status': '発表'}]
                }]
            }
        }]

        warnings, report_datetime = app_module.parse_area_warnings(warning_data)

        self.assertEqual(report_datetime, '2026-09-02T11:17:00+09:00')
        self.assertEqual({w['code'] for w in warnings}, {'14', '43'})
        self.assertIn('雷注意報', [w['name'] for w in warnings])
        self.assertIn('レベル4大雨危険警報', [w['name'] for w in warnings])


if __name__ == '__main__':
    unittest.main()
