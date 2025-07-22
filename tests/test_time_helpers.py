import pytest
import datetime
import time
import pytz
from unittest.mock import Mock, patch

# Import the modules to test
from modules.time_helpers import (
    get_current_datetime_tz_aware, get_current_datetime, get_current_time_as_str,
    get_current_time_as_str_hhmmss, get_current_datetime_as_str, get_time_from_str,
    get_ist_datetime_from_naive_dt_str, get_ist_datetime_obj_from_naive_dt_obj,
    get_datetime_from_str, INDIAN_TZ, IST
)


class TestTimeHelpers:
    """Unit tests for time helper functions"""
    
    def test_constants(self):
        """Test that timezone constants are properly defined"""
        assert INDIAN_TZ == 'Asia/Kolkata'
        assert IST.zone == 'Asia/Kolkata'
        assert isinstance(IST, pytz.tzinfo.DstTzInfo)
    
    def test_get_current_datetime_tz_aware(self):
        """Test get_current_datetime_tz_aware returns timezone-aware datetime"""
        result = get_current_datetime_tz_aware()
        
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is not None
        assert result.tzinfo.zone == 'Asia/Kolkata'
        # Should return current time, so just verify it's recent
        now = datetime.datetime.now()
        assert abs((result.replace(tzinfo=None) - now).total_seconds()) < 5
    
    def test_get_current_datetime(self):
        """Test get_current_datetime returns IST datetime"""
        result = get_current_datetime()
        
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is not None
        assert result.tzinfo.zone == 'Asia/Kolkata'
        # Should return current time, so just verify it's recent
        now = datetime.datetime.now()
        assert abs((result.replace(tzinfo=None) - now).total_seconds()) < 5
    
    def test_get_current_time_as_str(self):
        """Test get_current_time_as_str returns formatted time string"""
        result = get_current_time_as_str()
        
        assert isinstance(result, str)
        # Should match HH:MM:SS format
        assert len(result) == 8
        assert result.count(':') == 2
        
        # Verify format with regex
        import re
        assert re.match(r'^\d{2}:\d{2}:\d{2}$', result)
    
    def test_get_current_time_as_str_hhmmss(self):
        """Test get_current_time_as_str_hhmmss returns formatted time string without colons"""
        result = get_current_time_as_str_hhmmss()
        
        assert isinstance(result, str)
        # Should match HHMMSS format (6 digits, no colons)
        assert len(result) == 6
        assert ':' not in result
        
        # Verify format with regex
        import re
        assert re.match(r'^\d{6}$', result)
    
    def test_get_current_datetime_as_str(self):
        """Test get_current_datetime_as_str returns formatted datetime string"""
        result = get_current_datetime_as_str()
        
        assert isinstance(result, str)
        # Should match YYYY-MM-DD HH:MM:SS format
        assert len(result) == 19
        
        # Verify format with regex
        import re
        assert re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', result)
    
    def test_get_time_from_str_valid_format(self):
        """Test get_time_from_str with valid time string"""
        time_str = "14:30:45"
        result = get_time_from_str(time_str)
        
        assert isinstance(result, datetime.datetime)
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        # Should be a datetime object with default date (1900-01-01)
        assert result.year == 1900
        assert result.month == 1
        assert result.day == 1
    
    def test_get_time_from_str_invalid_format(self):
        """Test get_time_from_str with invalid time string"""
        with pytest.raises(ValueError):
            get_time_from_str("invalid_time")
        
        with pytest.raises(ValueError):
            get_time_from_str("25:30:45")  # Invalid hour
        
        with pytest.raises(ValueError):
            get_time_from_str("14:60:45")  # Invalid minute
        
        with pytest.raises(ValueError):
            get_time_from_str("14:30:60")  # Invalid second
    
    def test_get_time_from_str_edge_cases(self):
        """Test get_time_from_str with edge case time values"""
        # Test midnight
        result = get_time_from_str("00:00:00")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        
        # Test end of day
        result = get_time_from_str("23:59:59")
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
    
    def test_get_ist_datetime_from_naive_dt_str_valid(self):
        """Test get_ist_datetime_from_naive_dt_str with valid datetime string"""
        dt_str = "2023-07-21 14:30:45"
        result = get_ist_datetime_from_naive_dt_str(dt_str)
        
        assert isinstance(result, datetime.datetime)
        assert result.year == 2023
        assert result.month == 7
        assert result.day == 21
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None
        assert result.tzinfo.zone == 'Asia/Kolkata'
    
    def test_get_ist_datetime_from_naive_dt_str_invalid(self):
        """Test get_ist_datetime_from_naive_dt_str with invalid datetime string"""
        with pytest.raises(ValueError):
            get_ist_datetime_from_naive_dt_str("invalid_datetime")
        
        with pytest.raises(ValueError):
            get_ist_datetime_from_naive_dt_str("2023-13-21 14:30:45")  # Invalid month
        
        with pytest.raises(ValueError):
            get_ist_datetime_from_naive_dt_str("2023-07-32 14:30:45")  # Invalid day
    
    def test_get_ist_datetime_obj_from_naive_dt_obj(self):
        """Test get_ist_datetime_obj_from_naive_dt_obj with datetime object"""
        # Create a naive datetime object
        naive_dt = datetime.datetime(2023, 7, 21, 14, 30, 45)
        
        result = get_ist_datetime_obj_from_naive_dt_obj(naive_dt)
        
        assert isinstance(result, datetime.datetime)
        assert result.year == 2023
        assert result.month == 7
        assert result.day == 21
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None
        assert result.tzinfo.zone == 'Asia/Kolkata'
    
    def test_get_ist_datetime_obj_from_naive_dt_obj_already_aware(self):
        """Test get_ist_datetime_obj_from_naive_dt_obj with already timezone-aware object"""
        # Create a timezone-aware datetime object
        utc_tz = pytz.timezone('UTC')
        aware_dt = datetime.datetime(2023, 7, 21, 14, 30, 45, tzinfo=utc_tz)
        
        result = get_ist_datetime_obj_from_naive_dt_obj(aware_dt)
        
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is not None
        assert result.tzinfo.zone == 'Asia/Kolkata'
        # Time should be converted from UTC to IST (UTC+5:30)
        # 14:30:45 UTC should become 20:00:45 IST
        assert result.hour == 20
        assert result.minute == 0
        assert result.second == 45
    
    def test_get_datetime_from_str_valid(self):
        """Test get_datetime_from_str with valid datetime string"""
        dt_str = "2023-07-21 14:30:45"
        result = get_datetime_from_str(dt_str)
        
        assert isinstance(result, datetime.datetime)
        assert result.year == 2023
        assert result.month == 7
        assert result.day == 21
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        # Should be naive (no timezone info)
        assert result.tzinfo is None
    
    def test_get_datetime_from_str_invalid(self):
        """Test get_datetime_from_str with invalid datetime string"""
        with pytest.raises(ValueError):
            get_datetime_from_str("invalid_datetime")
        
        with pytest.raises(ValueError):
            get_datetime_from_str("2023-13-21 14:30:45")  # Invalid month
        
        with pytest.raises(ValueError):
            get_datetime_from_str("2023-07-32 14:30:45")  # Invalid day
        
        with pytest.raises(ValueError):
            get_datetime_from_str("2023-07-21 25:30:45")  # Invalid hour
    
    def test_get_datetime_from_str_edge_cases(self):
        """Test get_datetime_from_str with edge case datetime values"""
        # Test leap year
        result = get_datetime_from_str("2024-02-29 12:00:00")
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29
        
        # Test end of year
        result = get_datetime_from_str("2023-12-31 23:59:59")
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 31
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
    
    def test_timezone_consistency(self):
        """Test that timezone-related functions use consistent timezone"""
        # All IST-related functions should use the same timezone
        dt1 = get_current_datetime()
        dt2 = get_current_datetime_tz_aware()
        
        assert dt1.tzinfo.zone == dt2.tzinfo.zone == 'Asia/Kolkata'
    
    def test_string_format_consistency(self):
        """Test that string formatting functions produce consistent formats"""
        # Get all time strings at roughly the same time
        time_str = get_current_time_as_str()
        time_str_no_colon = get_current_time_as_str_hhmmss()
        datetime_str = get_current_datetime_as_str()
        
        # Extract time part from datetime string
        datetime_time_part = datetime_str.split(' ')[1]
        
        # Time strings should be consistent (allowing for small time differences)
        assert time_str_no_colon == time_str.replace(':', '')
        # The datetime time part should be very close to the standalone time
        assert len(time_str) == len(datetime_time_part) == 8
    
    def test_round_trip_conversions(self):
        """Test round-trip conversions between string and datetime formats"""
        original_dt_str = "2023-07-21 14:30:45"
        original_time_str = "14:30:45"
        
        # Test datetime round-trip
        dt_obj = get_datetime_from_str(original_dt_str)
        converted_back = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        assert converted_back == original_dt_str
        
        # Test time round-trip
        time_obj = get_time_from_str(original_time_str)
        time_back = time_obj.strftime("%H:%M:%S")
        assert time_back == original_time_str
    
    def test_none_input_handling(self):
        """Test functions handle None input appropriately"""
        with pytest.raises((TypeError, AttributeError)):
            get_ist_datetime_obj_from_naive_dt_obj(None)
        
        with pytest.raises((TypeError, ValueError)):
            get_time_from_str(None)
        
        with pytest.raises((TypeError, ValueError)):
            get_datetime_from_str(None)
        
        with pytest.raises((TypeError, ValueError)):
            get_ist_datetime_from_naive_dt_str(None)


if __name__ == '__main__':
    pytest.main([__file__])
