"""
Description: This module provides a base service for handling HTTP API requests.

Changelog:
- 2025-03-07: Initial Creation.
"""

import requests


class BaseService:
    """Base HTTP service to handle API requests"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None  # Store authentication token

    def set_auth_token(self, token):
        """Set authentication token"""
        self.auth_token = token

    def _get_headers(self, headers=None):
        """Construct request headers, automatically add token"""
        default_headers = {"Content-Type": "application/json"}
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        if headers:
            default_headers.update(headers)
        return default_headers

    def post(self, endpoint, data=None, headers=None):
        """Send POST request"""
        # self.logger.log_info(f"POST {endpoint} - DATA: {data}")
        return self._send_request("POST", endpoint, data, headers)

    def get(self, endpoint, headers=None):
        """Send GET request"""
        # self.logger.log_info(f"GET {endpoint}")
        return self._send_request("GET", endpoint, None, headers)

    def put(self, endpoint, data=None, headers=None):
        """Send PUT request"""
        # self.logger.log_info(f"PUT {endpoint} - DATA: {data}")
        return self._send_request("PUT", endpoint, data, headers)

    def delete(self, endpoint, headers=None):
        """Send DELETE request"""
        # self.logger.log_info(f"DELETE {endpoint}")
        return self._send_request("DELETE", endpoint, None, headers)

    def _send_request(self, method, endpoint, data=None, headers=None):
        """Generic HTTP request method"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, url, json=data, headers=self._get_headers(headers)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # self.logger.log_error(f"Request error: {e}")
            return None
