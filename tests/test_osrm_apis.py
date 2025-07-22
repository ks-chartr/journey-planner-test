import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import json

# Import the modules to test
from modules.osrm_apis import (
    make_call_drive, make_call_walk
)


class TestOSRMAPIs:
    """Unit tests for OSRM API functions"""
    
    def test_make_call_drive_success(self):
        """Test make_call_drive with successful API response"""
        source = (28.6139, 77.2090)  # lat, lon
        destination = (28.6562, 77.2410)
        
        mock_response = {
            "routes": [
                {
                    "distance": 5000.0,
                    "duration": 600.0,
                    "geometry": "test_geometry"
                }
            ],
            "code": "Ok"
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = make_call_drive(source, destination)
            
            assert result == mock_response
            assert "routes" in result
            assert result["code"] == "Ok"
            
            # Verify the URL was constructed correctly
            expected_url = f'http://osrm.chartr.in/route/v1/driving/{source[1]},{source[0]};{destination[1]},{destination[0]}?steps=false&alternatives=true'
            mock_get.assert_called_once_with(expected_url, timeout=5)
    
    def test_make_call_drive_http_error(self):
        """Test make_call_drive with HTTP error response"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            result = make_call_drive(source, destination)
            
            assert result == {}
    
    def test_make_call_drive_timeout(self):
        """Test make_call_drive with timeout exception"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = make_call_drive(source, destination)
            
            assert result == {}
    
    def test_make_call_drive_request_exception(self):
        """Test make_call_drive with general request exception"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection error")
            
            result = make_call_drive(source, destination)
            
            assert result == {}
    
    def test_make_call_drive_invalid_coordinates(self):
        """Test make_call_drive with invalid coordinates"""
        # Test with None values
        with pytest.raises((TypeError, AttributeError)):
            make_call_drive(None, (28.6562, 77.2410))
        
        with pytest.raises((TypeError, AttributeError)):
            make_call_drive((28.6139, 77.2090), None)
    
    def test_make_call_drive_empty_coordinates(self):
        """Test make_call_drive with empty coordinate tuples"""
        with pytest.raises(IndexError):
            make_call_drive((), (28.6562, 77.2410))
        
        with pytest.raises(IndexError):
            make_call_drive((28.6139, 77.2090), ())
    
    def test_make_call_walk_success(self):
        """Test make_call_walk with successful API response"""
        source = (28.6139, 77.2090)  # lat, lon
        destination = (28.6562, 77.2410)
        
        mock_response = {
            "routes": [
                {
                    "distance": 2000.0,
                    "duration": 1200.0,
                    "geometry": "test_geometry"
                }
            ],
            "code": "Ok"
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = make_call_walk(source, destination)
            
            assert result == mock_response
            assert "routes" in result
            assert result["code"] == "Ok"
            
            # Verify the URL was constructed correctly (note: foot instead of driving, alternatives=false)
            expected_url = f'http://osrm.chartr.in/route/v1/foot/{source[1]},{source[0]};{destination[1]},{destination[0]}?steps=false&alternatives=false'
            mock_get.assert_called_once_with(expected_url, timeout=5)
    
    def test_make_call_walk_http_error(self):
        """Test make_call_walk with HTTP error response"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 500
            
            result = make_call_walk(source, destination)
            
            assert result == {}
    
    def test_make_call_walk_timeout(self):
        """Test make_call_walk with timeout exception"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = make_call_walk(source, destination)
            
            assert result == {}
    
    def test_make_call_walk_request_exception(self):
        """Test make_call_walk with general request exception"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            result = make_call_walk(source, destination)
            
            assert result == {}
    
    def test_make_call_walk_invalid_coordinates(self):
        """Test make_call_walk with invalid coordinates"""
        # Test with None values
        with pytest.raises((TypeError, AttributeError)):
            make_call_walk(None, (28.6562, 77.2410))
        
        with pytest.raises((TypeError, AttributeError)):
            make_call_walk((28.6139, 77.2090), None)
    
    def test_make_call_walk_coordinate_format_validation(self):
        """Test both functions handle coordinate format correctly"""
        source = (28.6139, 77.2090)  # (lat, lon)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"code": "Ok"}
            
            # Test drive call
            make_call_drive(source, destination)
            drive_call_args = mock_get.call_args[0][0]
            
            # URL should have lon,lat format (reversed from input)
            assert f"{source[1]},{source[0]}" in drive_call_args
            assert f"{destination[1]},{destination[0]}" in drive_call_args
            
            mock_get.reset_mock()
            
            # Test walk call
            make_call_walk(source, destination)
            walk_call_args = mock_get.call_args[0][0]
            
            # URL should have lon,lat format (reversed from input)
            assert f"{source[1]},{source[0]}" in walk_call_args
            assert f"{destination[1]},{destination[0]}" in walk_call_args
    
    def test_make_call_drive_vs_walk_url_differences(self):
        """Test the URL differences between drive and walk calls"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"code": "Ok"}
            
            # Test drive call
            make_call_drive(source, destination)
            drive_url = mock_get.call_args[0][0]
            
            # Drive should use 'driving' and 'alternatives=true'
            assert 'driving' in drive_url
            assert 'alternatives=true' in drive_url
            
            mock_get.reset_mock()
            
            # Test walk call
            make_call_walk(source, destination)
            walk_url = mock_get.call_args[0][0]
            
            # Walk should use 'foot' and 'alternatives=false'
            assert 'foot' in walk_url
            assert 'alternatives=false' in walk_url
    
    def test_coordinate_boundary_values(self):
        """Test functions with boundary coordinate values"""
        # Test with extreme but valid coordinates
        extreme_source = (-90.0, -180.0)  # South pole, international date line
        extreme_dest = (90.0, 180.0)      # North pole, international date line
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"code": "Ok"}
            
            # Should not raise exceptions
            result_drive = make_call_drive(extreme_source, extreme_dest)
            result_walk = make_call_walk(extreme_source, extreme_dest)
            
            assert result_drive == {"code": "Ok"}
            assert result_walk == {"code": "Ok"}
    
    def test_json_parsing_error(self):
        """Test handling of JSON parsing errors"""
        source = (28.6139, 77.2090)
        destination = (28.6562, 77.2410)
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            # Should handle JSON decode error gracefully
            with pytest.raises(json.JSONDecodeError):
                make_call_drive(source, destination)
            
            with pytest.raises(json.JSONDecodeError):
                make_call_walk(source, destination)


if __name__ == '__main__':
    pytest.main([__file__])
