#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""Test the DateAccessor object."""
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

import dateutil
from django.conf import settings
from faker import Faker

from api.utils import DateHelper
from masu.config import Config
from masu.external.date_accessor import DateAccessor
from masu.external.date_accessor import DateAccessorError
from masu.test import MasuTestCase


class DateAccessorTest(MasuTestCase):
    """Test Cases for the DateAccessor object."""

    fake = Faker()

    @classmethod
    def setUpClass(cls):
        """Class initialization."""
        super().setUpClass()
        cls.initial_debug = Config.DEBUG
        cls.initial_override = Config.MASU_DATE_OVERRIDE

    @classmethod
    def tearDownClass(cls):
        """Class Teardown."""
        super().tearDownClass()
        Config.DEBUG = cls.initial_debug
        Config.MASU_DATE_OVERRIDE = cls.initial_override

    def setUp(self):
        """Set up the tests."""
        DateAccessor.mock_date_time = None
        DateAccessor.date_time_last_accessed = datetime.now(tz=settings.UTC)
        Config.DEBUG = False
        Config.MASU_DATE_OVERRIDE = None

    def test_today_override(self):
        """Test today() with override."""
        fake_dt = self.fake.date_time(tzinfo=settings.UTC)
        Config.DEBUG = True
        Config.MASU_DATE_OVERRIDE = fake_dt.strftime("%Y-%m-%d %H:%M:%S")

        accessor = DateAccessor()
        today = accessor.today()

        self.assertEqual(today.year, fake_dt.year)
        self.assertEqual(today.month, fake_dt.month)
        self.assertEqual(today.day, fake_dt.day)
        self.assertEqual(today.tzinfo.tzname(today), str(settings.UTC))

    def test_today_override_debug_false(self):
        """Test today() with override when debug is false."""
        fake_tz = ZoneInfo(self.fake.timezone())
        fake_dt = self.fake.date_time(tzinfo=fake_tz)
        Config.DEBUG = False
        Config.MASU_DATE_OVERRIDE = fake_dt

        accessor = DateAccessor()
        today = accessor.today()
        expected_date = datetime.now(tz=settings.UTC)

        self.assertEqual(today.year, expected_date.year)
        self.assertEqual(today.month, expected_date.month)
        self.assertEqual(today.day, expected_date.day)
        self.assertEqual(today.tzinfo, settings.UTC)

    def test_today_override_override_not_set(self):
        """Test today() with override set when debug is true."""
        Config.DEBUG = True
        Config.MASU_DATE_OVERRIDE = None

        accessor = DateAccessor()
        today = accessor.today()
        expected_date = datetime.now(tz=settings.UTC)

        self.assertEqual(today.year, expected_date.year)
        self.assertEqual(today.month, expected_date.month)
        self.assertEqual(today.day, expected_date.day)
        self.assertEqual(today.tzinfo, settings.UTC)

    def test_today_override_override_not_set_debug_false(self):
        """Test today() with override not set when debug is false."""
        Config.DEBUG = False
        Config.MASU_DATE_OVERRIDE = None

        accessor = DateAccessor()
        today = accessor.today()
        expected_date = datetime.now(tz=settings.UTC)

        self.assertEqual(today.year, expected_date.year)
        self.assertEqual(today.month, expected_date.month)
        self.assertEqual(today.day, expected_date.day)
        self.assertEqual(today.tzinfo, settings.UTC)

    def test_today_override_with_iso8601(self):
        """Test today() with override and using ISO8601 format."""

        # Use timezones with UTC offset of something other than 0 to avoid test failures.
        # dateutil.parse() returns incorrect zone offset information when the timezone string is 00:00.
        timezones = (
            "America/Anchorage",
            "America/New_York",
            "Europe/Berlin",
            "Indian/Maldives",
            "Pacific/Fiji",
            "Pacific/Palau",
        )
        fake_tz_name = secrets.choice(timezones)
        fake_tz = ZoneInfo(fake_tz_name)
        fake_dt = self.fake.date_time(tzinfo=fake_tz)

        Config.DEBUG = True
        Config.MASU_DATE_OVERRIDE = fake_dt.isoformat()
        accessor = DateAccessor()
        today = accessor.today()

        self.assertEqual(today.year, fake_dt.year)
        self.assertEqual(today.month, fake_dt.month)
        self.assertEqual(today.day, fake_dt.day)

        expected_offset = dateutil.tz.tzoffset(fake_tz_name, fake_tz.utcoffset(fake_dt))
        self.assertEqual(today.tzinfo, expected_offset)

    def test_today_with_timezone_string(self):
        """Test that a timezone string works as expected."""
        string_tz = "UTC"
        current_utc_time = datetime.utcnow()
        accessor = DateAccessor()
        result_time = accessor.today_with_timezone(string_tz)

        self.assertEqual(current_utc_time.date(), result_time.date())
        self.assertEqual(current_utc_time.hour, result_time.hour)
        self.assertEqual(current_utc_time.minute, result_time.minute)
        self.assertEqual(result_time.tzinfo, settings.UTC)

    def test_today_with_timezone_object(self):
        """Test that a timezone string works as expected."""
        fake_tz_name = self.fake.timezone()
        fake_tz = ZoneInfo(fake_tz_name)

        current_time = datetime.now(fake_tz)
        accessor = DateAccessor()
        result_time = accessor.today_with_timezone(fake_tz)

        self.assertEqual(current_time.date(), result_time.date())
        self.assertEqual(current_time.hour, result_time.hour)
        self.assertEqual(current_time.minute, result_time.minute)
        self.assertEqual(str(result_time.tzinfo), fake_tz_name)

    def test_today_with_timezone_error_raised(self):
        """Test that an error is raised with an invalid timezone."""
        string_tz = "Moon/Mare Tranquillitatis"
        accessor = DateAccessor()

        with self.assertRaises(DateAccessorError):
            accessor.today_with_timezone(string_tz)

    def test_get_billing_month_start(self):
        """Test that a proper datetime is returend for bill month."""
        dh = DateHelper()
        accessor = DateAccessor()
        expected = dh.this_month_start.date()
        today = dh.today
        str_input = str(today)
        datetime_input = today
        date_input = today.date()
        self.assertEqual(accessor.get_billing_month_start(str_input), expected)
        self.assertEqual(accessor.get_billing_month_start(datetime_input), expected)
        self.assertEqual(accessor.get_billing_month_start(date_input), expected)
