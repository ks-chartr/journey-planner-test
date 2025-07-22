import pytest
import requests
from unittest.mock import Mock, patch
import json

# Import the modules to test
from modules.metro_station_info_api import get_station_info


class TestMetroStationInfoAPI:
    """Unit tests for metro station info API functions"""
    
    def setup_method(self):
        """Clear the LRU cache before each test"""
        get_station_info.cache_clear()
    
    def test_get_station_info_success(self):
        """Test get_station_info with successful API response"""
        station_code = 'GDPI'
        
        mock_response = {
            "station_code": "GDPI",
            "station_name": "Govind Puri",
            "line": "Violet Line",
            "platforms": [
                {
                    "platform_name": "Platform 1",
                    "train_towards": {"station_name": "Kashmere Gate"}
                },
                {
                    "platform_name": "Platform 2", 
                    "train_towards": {"station_name": "Badarpur Border"}
                }
            ]
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = get_station_info(station_code)
            
            assert result == mock_response
            assert result["station_code"] == "GDPI"
            assert result["station_name"] == "Govind Puri"
            assert "platforms" in result
            
            # Verify the URL was constructed correctly
            expected_url = f'https://delhi-metro-api.chartr.in/station/{station_code}'
            mock_get.assert_called_once_with(expected_url, timeout=5)
    
    def test_get_station_info_http_error(self):
        """Test get_station_info with HTTP error response"""
        station_code = 'INVALID'
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            result = get_station_info(station_code)
            
            assert result == {}
    
    def test_get_station_info_server_error(self):
        """Test get_station_info with server error response"""
        station_code = 'INVALID_CODE'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.return_value.status_code = 500
            
            result = get_station_info(station_code)
            
            assert result == {}
    
    def test_get_station_info_timeout(self):
        """Test get_station_info with timeout exception"""
        station_code = 'TIMEOUT_TEST'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = get_station_info(station_code)
            
            assert result == {}
    
    def test_get_station_info_request_exception(self):
        """Test get_station_info with general request exception"""
        station_code = 'REQ_ERROR_TEST'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            result = get_station_info(station_code)
            
            assert result == {}
    
    def test_get_station_info_connection_error(self):
        """Test get_station_info with connection error"""
        station_code = 'CONN_ERROR_TEST'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            result = get_station_info(station_code)
            
            assert result == {}
    
    def test_get_station_info_json_decode_error(self):
        """Test get_station_info with JSON decode error"""
        station_code = 'JSON_ERROR_TEST'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            with pytest.raises(json.JSONDecodeError):
                get_station_info(station_code)
    
    def test_get_station_info_empty_station_code(self):
        """Test get_station_info with empty station code"""
        station_code = ''
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            
            result = get_station_info(station_code)
            
            # Should still make the API call
            expected_url = f'https://delhi-metro-api.chartr.in/station/{station_code}'
            mock_get.assert_called_once_with(expected_url, timeout=5)
            assert result == {}
    
    def test_get_station_info_none_station_code(self):
        """Test get_station_info with None station code"""
        station_code = None
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            
            result = get_station_info(station_code)
            
            # Should still make the API call with None converted to string
            expected_url = f'https://delhi-metro-api.chartr.in/station/{station_code}'
            mock_get.assert_called_once_with(expected_url, timeout=5)
            assert result == {}
    
    def test_get_station_info_special_characters(self):
        """Test get_station_info with special characters in station code"""
        station_code = 'TEST@#$'
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"station_code": station_code}
            
            result = get_station_info(station_code)
            
            # Should handle special characters in URL
            expected_url = f'https://delhi-metro-api.chartr.in/station/{station_code}'
            mock_get.assert_called_once_with(expected_url, timeout=5)
            assert result == {"station_code": station_code}
    
    def test_get_station_info_caching_behavior(self):
        """Test that get_station_info uses LRU cache correctly"""
        station_code = 'CACHE_TEST'
        
        mock_response = {
            "station_code": "CACHE_TEST",
            "station_name": "Cache Test Station"
        }
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            # First call
            result1 = get_station_info(station_code)
            
            # Second call with same station code
            result2 = get_station_info(station_code)
            
            # Both results should be the same
            assert result1 == result2 == mock_response
            
            # Due to caching, requests.get should only be called once
            assert mock_get.call_count == 1
    
    def test_get_station_info_different_station_codes(self):
        """Test get_station_info with different station codes"""
        station_code1 = 'DIFF_TEST_1'
        station_code2 = 'DIFF_TEST_2'
        
        mock_response1 = {"station_code": "DIFF_TEST_1", "station_name": "Test Station 1"}
        mock_response2 = {"station_code": "DIFF_TEST_2", "station_name": "Test Station 2"}
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            # Setup different responses for different calls
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.side_effect = [mock_response1, mock_response2]
            
            result1 = get_station_info(station_code1)
            result2 = get_station_info(station_code2)
            
            assert result1 == mock_response1
            assert result2 == mock_response2
            
            # Should make two separate API calls for different station codes
            assert mock_get.call_count == 2
    
    def test_get_station_info_url_construction(self):
        """Test that URL is constructed correctly for various station codes"""
        test_cases = [
            'URL_TEST_1',
            'URL_TEST_2', 
            'URL_TEST_3',
            'URL_TEST_4',
            'URL_TEST_5',
            'URL_TEST_6'
        ]
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            
            for station_code in test_cases:
                get_station_info(station_code)
                
                expected_url = f'https://delhi-metro-api.chartr.in/station/{station_code}'
                mock_get.assert_called_with(expected_url, timeout=5)
                
                # Clear cache and reset mock for next iteration
                get_station_info.cache_clear()
                mock_get.reset_mock()
    
    def test_get_station_info_timeout_value(self):
        """Test that the correct timeout value is used"""
        station_code = 'TIMEOUT_VAL_TEST'
        
        with patch('modules.metro_station_info_api.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}
            
            get_station_info(station_code)
            
            # Verify timeout is set to 5 seconds
            args, kwargs = mock_get.call_args
            assert kwargs.get('timeout') == 5


if __name__ == '__main__':
    pytest.main([__file__])
