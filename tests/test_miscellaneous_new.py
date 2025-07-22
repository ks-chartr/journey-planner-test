import pytest
import pandas as pd
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
import math
import json
import datetime

# Import the modules to test
from modules.miscellaneous import (
    haversine_distance, access_with_handle, get_column_from_df_as_list,
    get_platform_info_details, get_peak_off_peak_category, get_frequency
)


class TestMiscellaneous:
    """Unit tests for miscellaneous utility functions"""
    
    def test_haversine_distance_valid_coordinates(self):
        """Test haversine_distance with valid coordinates"""
        # Test distance between two points in Delhi
        lat1, lon1 = 28.6139, 77.2090  # New Delhi
        lat2, lon2 = 28.6562, 77.2410  # Red Fort
        
        result = haversine_distance(lat1, lon1, lat2, lon2)
        
        assert isinstance(result, (int, float))
        assert result >= 0
        # Should be a reasonable distance (few kilometers)
        assert result < 100  # Less than 100 km
        assert result > 0    # Should be greater than 0 for different points
    
    def test_haversine_distance_same_point(self):
        """Test haversine_distance with same coordinates"""
        lat, lon = 28.6139, 77.2090
        
        result = haversine_distance(lat, lon, lat, lon)
        
        assert result == 0.0 or result < 0.001  # Should be 0 or very close to 0
    
    def test_haversine_distance_known_distance(self):
        """Test haversine_distance with known distance"""
        # Test with coordinates that have a known approximate distance
        # Delhi to Mumbai (approximate coordinates)
        delhi_lat, delhi_lon = 28.6139, 77.2090
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        
        result = haversine_distance(delhi_lat, delhi_lon, mumbai_lat, mumbai_lon)
        
        # Distance between Delhi and Mumbai is approximately 1150-1200 km
        assert 1000 < result < 1400  # Allow some tolerance
    
    def test_haversine_distance_invalid_coordinates(self):
        """Test haversine_distance with invalid coordinates"""
        # Test with None values
        with pytest.raises((TypeError, AttributeError)):
            haversine_distance(None, 77.2090, 28.6562, 77.2410)
        
        with pytest.raises((TypeError, AttributeError)):
            haversine_distance(28.6139, None, 28.6562, 77.2410)
    
    def test_haversine_distance_extreme_coordinates(self):
        """Test haversine_distance with extreme coordinates"""
        # Test with coordinates at poles and equator
        north_pole_lat, north_pole_lon = 90.0, 0.0
        south_pole_lat, south_pole_lon = -90.0, 0.0
        
        result = haversine_distance(north_pole_lat, north_pole_lon, south_pole_lat, south_pole_lon)
        
        # Distance between poles should be approximately half Earth's circumference
        assert 19000 < result < 21000  # Approximately 20,000 km
    
    def test_access_with_handle_success_no_args(self):
        """Test access_with_handle with successful execution without args"""
        mock_loader = Mock(return_value="test_result")
        
        result = access_with_handle(
            env="test_env",
            load_using=mock_loader,
            exception=FileNotFoundError,
            place_holder="default",
            args=False
        )
        
        assert result == "test_result"
        mock_loader.assert_called_once_with("test_env")
    
    def test_access_with_handle_success_with_args(self):
        """Test access_with_handle with successful execution with args"""
        mock_loader = Mock(return_value="test_result")
        
        result = access_with_handle(
            env="test_env",
            load_using=mock_loader,
            exception=FileNotFoundError,
            place_holder="default",
            args=True,
            arg1="value1",
            kwarg1="kwvalue1"
        )
        
        assert result == "test_result"
        mock_loader.assert_called_once_with("test_env", arg1="value1", kwarg1="kwvalue1")
    
    def test_access_with_handle_exception_not_must(self):
        """Test access_with_handle with exception when must=False"""
        mock_loader = Mock(side_effect=FileNotFoundError("File not found"))
        
        result = access_with_handle(
            env="test_env",
            load_using=mock_loader,
            exception=FileNotFoundError,
            place_holder="default_value",
            must=False
        )
        
        assert result == "default_value"
    
    def test_access_with_handle_exception_must_true(self):
        """Test access_with_handle with exception when must=True"""
        mock_loader = Mock(side_effect=FileNotFoundError("File not found"))
        
        with pytest.raises(Exception, match="Make sure env: test_env is not present"):
            access_with_handle(
                env="test_env",
                load_using=mock_loader,
                exception=FileNotFoundError,
                place_holder="default_value",
                must=True
            )
    
    def test_get_column_from_df_as_list_success(self):
        """Test get_column_from_df_as_list with valid dataframe and column"""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        result = get_column_from_df_as_list(df, 'col1')
        
        assert result == [1, 2, 3]
        assert isinstance(result, list)
    
    def test_get_column_from_df_as_list_missing_column(self):
        """Test get_column_from_df_as_list with missing column"""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        result = get_column_from_df_as_list(df, 'nonexistent_column')
        
        assert result == []
        assert isinstance(result, list)
    
    def test_get_column_from_df_as_list_empty_dataframe(self):
        """Test get_column_from_df_as_list with empty dataframe"""
        df = pd.DataFrame()
        
        result = get_column_from_df_as_list(df, 'any_column')
        
        assert result == []
        assert isinstance(result, list)
    
    def test_get_peak_off_peak_category_early_morning(self):
        """Test get_peak_off_peak_category for early morning hours"""
        result = get_peak_off_peak_category(5)
        assert result == "non_peak_1"
        
        result = get_peak_off_peak_category(7)
        assert result == "non_peak_1"
    
    def test_get_peak_off_peak_category_morning_peak(self):
        """Test get_peak_off_peak_category for morning peak hours"""
        result = get_peak_off_peak_category(8)
        assert result == "peak_1"
        
        result = get_peak_off_peak_category(10)
        assert result == "peak_1"
        
        result = get_peak_off_peak_category(11)
        assert result == "peak_1"
    
    def test_get_peak_off_peak_category_afternoon_non_peak(self):
        """Test get_peak_off_peak_category for afternoon non-peak hours"""
        result = get_peak_off_peak_category(12)
        assert result == "non_peak_2"
        
        result = get_peak_off_peak_category(15)
        assert result == "non_peak_2"
        
        result = get_peak_off_peak_category(16)
        assert result == "non_peak_2"
    
    def test_get_peak_off_peak_category_evening_peak(self):
        """Test get_peak_off_peak_category for evening peak hours"""
        result = get_peak_off_peak_category(17)
        assert result == "peak_2"
        
        result = get_peak_off_peak_category(19)
        assert result == "peak_2"
        
        result = get_peak_off_peak_category(20)
        assert result == "peak_2"
    
    def test_get_peak_off_peak_category_night_non_peak(self):
        """Test get_peak_off_peak_category for night non-peak hours"""
        result = get_peak_off_peak_category(21)
        assert result == "non_peak_3"
        
        result = get_peak_off_peak_category(23)
        assert result == "non_peak_3"
        
        # Hour 0 falls into the first condition (< 8), so it's non_peak_1
        result = get_peak_off_peak_category(0)
        assert result == "non_peak_1"
    
    def test_get_peak_off_peak_category_boundary_values(self):
        """Test get_peak_off_peak_category for boundary values"""
        # Test exact boundary values
        assert get_peak_off_peak_category(8) == "peak_1"
        assert get_peak_off_peak_category(7.9) == "non_peak_1"
        assert get_peak_off_peak_category(12) == "non_peak_2"
        assert get_peak_off_peak_category(11.9) == "peak_1"
        assert get_peak_off_peak_category(17) == "peak_2"
        assert get_peak_off_peak_category(16.9) == "non_peak_2"
        assert get_peak_off_peak_category(21) == "non_peak_3"
        assert get_peak_off_peak_category(20.9) == "peak_2"
    
    @patch('modules.miscellaneous.frequencies')
    def test_get_frequency_success(self, mock_frequencies):
        """Test get_frequency with successful frequency lookup"""
        # Mock the frequencies dataframe with proper filtering behavior
        mock_df = pd.DataFrame({
            'route_id': [1, 1, 2, 2],
            'time_category': ['peak_1', 'non_peak_1', 'peak_1', 'non_peak_1'],
            'frequency': [10, 15, 8, 12]
        })
        
        # Mock the loc filtering to return the correct row
        filtered_result = mock_df[(mock_df.route_id == 1) & (mock_df.time_category == 'peak_1')]
        mock_frequencies.loc.__getitem__.return_value = filtered_result
        mock_frequencies.empty = False
        
        # Mock squeeze to return the frequency value
        with patch.object(filtered_result, 'squeeze', return_value=10):
            result = get_frequency(1, '10:00:00')
            assert result == 10
    
    @patch('modules.miscellaneous.frequencies')
    def test_get_frequency_no_query_time(self, mock_frequencies):
        """Test get_frequency without query_time (uses current hour)"""
        # Mock the frequencies dataframe
        mock_df = pd.DataFrame({
            'route_id': [1, 1],
            'time_category': ['peak_1', 'non_peak_1'],
            'frequency': [10, 15]
        })
        
        # Mock the loc filtering to return the correct row
        filtered_result = mock_df[(mock_df.route_id == 1) & (mock_df.time_category == 'peak_1')]
        mock_frequencies.loc.__getitem__.return_value = filtered_result
        mock_frequencies.empty = False
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 10  # Peak hour
            with patch.object(filtered_result, 'squeeze', return_value=10):
                result = get_frequency(1)
                assert result == 10
    
    @patch('modules.miscellaneous.frequencies')
    def test_get_frequency_route_not_found(self, mock_frequencies):
        """Test get_frequency with route not found"""
        # Mock empty result
        mock_frequencies.loc = Mock(side_effect=Exception("No data found"))
        mock_frequencies.empty = False
        
        result = get_frequency(999, '10:00:00')
        
        assert result == -1
    
    @patch('modules.miscellaneous.frequencies')
    def test_get_frequency_empty_dataframe(self, mock_frequencies):
        """Test get_frequency with empty frequencies dataframe"""
        mock_frequencies.empty = True
        mock_frequencies.loc = Mock(side_effect=Exception("Empty dataframe"))
        
        result = get_frequency(1, '10:00:00')
        
        assert result == -1
    
    def test_get_frequency_invalid_time_format(self):
        """Test get_frequency with invalid time format"""
        with pytest.raises((ValueError, IndexError)):
            get_frequency(1, 'invalid_time')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_platform_info_details_success(self, mock_json_load, mock_file):
        """Test get_platform_info_details with successful platform lookup"""
        # Mock JSON response
        mock_json_load.return_value = {
            'platforms': [
                {
                    'platform_name': 'Platform 1',
                    'train_towards': {'station_name': 'Huda City Centre'}
                },
                {
                    'platform_name': 'Platform 2',
                    'train_towards': {'station_name': 'Dwarka Mor'}
                }
            ]
        }
        
        result = get_platform_info_details('Adarsh Nagar', 'Huda City Centre')
        
        assert result == 'Platform 1'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_platform_info_details_no_match(self, mock_json_load, mock_file):
        """Test get_platform_info_details with no matching platform"""
        # Mock JSON response
        mock_json_load.return_value = {
            'platforms': [
                {
                    'platform_name': 'Platform 1',
                    'train_towards': {'station_name': 'Some Other Station'}
                }
            ]
        }
        
        result = get_platform_info_details('Adarsh Nagar', 'Non-existent Station')
        
        assert result is None
    
    def test_get_platform_info_details_invalid_station(self):
        """Test get_platform_info_details with invalid station name"""
        result = get_platform_info_details('Invalid Station Name', 'Any Terminal')
        
        assert result is None
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_platform_info_details_file_not_found(self, mock_file):
        """Test get_platform_info_details with file not found"""
        with pytest.raises(FileNotFoundError):
            get_platform_info_details('Adarsh Nagar', 'Huda City Centre')
    
    def test_get_platform_info_details_case_insensitive(self):
        """Test get_platform_info_details is case insensitive for station names"""
        # Test with different cases
        with patch('builtins.open', mock_open()):
            with patch('json.load') as mock_json_load:
                mock_json_load.return_value = {
                    'platforms': [
                        {
                            'platform_name': 'Platform 1',
                            'train_towards': {'station_name': 'HUDA CITY CENTRE'}
                        }
                    ]
                }
                
                result = get_platform_info_details('ADARSH NAGAR', 'huda city centre')
                assert result == 'Platform 1'


if __name__ == '__main__':
    pytest.main([__file__])
