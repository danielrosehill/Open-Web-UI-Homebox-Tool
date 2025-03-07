"""
title: Homebox Inventory Search
author: Daniel Rosehill
author_url: https://github.com/danielrosehill
git_url: https://github.com/danielrosehill/Open-Web-UI-Homebox-Tool
description: Search for items in your homebox inventory
required_open_webui_version: 0.4.0
requirements: requests
version: 1.0.0
license: MIT
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        homebox_url: str = Field(
            default="", 
            description="Your Homebox API URL (e.g., https://homebox.yourdomain.com/api)"
        )
        cf_client_id: str = Field(
            default="", 
            description="Your Cloudflare Access Client ID (optional, required if behind Cloudflare Access)"
        )
        cf_client_secret: str = Field(
            default="", 
            description="Your Cloudflare Access Client Secret (optional, required if behind Cloudflare Access)"
        )
    
    def __init__(self):
        """Initialize the Tool."""
        self.valves = self.Valves()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests, including Cloudflare Access headers if provided.
        
        :return: Dictionary of headers for API requests
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add Cloudflare Access headers if provided
        if self.valves.cf_client_id and self.valves.cf_client_secret:
            headers["CF-Access-Client-Id"] = self.valves.cf_client_id
            headers["CF-Access-Client-Secret"] = self.valves.cf_client_secret
        
        return headers
    
    def search_items(self, query: str, page: int = 1, page_size: int = 20) -> str:
        """
        Search for items in the homebox inventory.
        
        :param query: Search query string
        :param page: Page number (default: 1)
        :param page_size: Number of items per page (default: 20)
        :return: A formatted string with the search results
        """
        if not self.valves.homebox_url:
            return "Error: Homebox API URL is required. Please set your Homebox API URL in the tool settings."
        
        # Ensure the URL has the correct format
        base_url = self.valves.homebox_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        endpoint = f"{base_url}/v1/items"
        params = {
            "q": query,
            "page": page,
            "pageSize": page_size
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                result = f"Found {data['total']} items matching '{query}':\n\n"
                
                for idx, item in enumerate(data['data'], 1):
                    result += f"{idx}. {item['name']}\n"
                    
                    if 'description' in item and item['description']:
                        result += f"   Description: {item['description']}\n"
                    
                    if 'location' in item and item['location']:
                        result += f"   Location: {item['location']['name']}\n"
                    
                    if 'assetId' in item and item['assetId']:
                        result += f"   Asset ID: {item['assetId']}\n"
                    
                    if 'quantity' in item:
                        result += f"   Quantity: {item['quantity']}\n"
                    
                    if 'manufacturer' in item and item['manufacturer']:
                        result += f"   Manufacturer: {item['manufacturer']}\n"
                    
                    if 'modelNumber' in item and item['modelNumber']:
                        result += f"   Model: {item['modelNumber']}\n"
                    
                    result += "\n"
                
                # Add pagination info
                total_pages = (data['total'] + page_size - 1) // page_size
                result += f"Page {page} of {total_pages}\n"
                
                if page < total_pages:
                    result += f"Use 'page={page+1}' to see more results."
                
                return result
            else:
                return f"No items found matching '{query}'."
        except requests.RequestException as e:
            return f"Error searching items: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def get_item_details(self, item_id: str) -> str:
        """
        Get detailed information about a specific item.
        
        :param item_id: The ID of the item to retrieve
        :return: A formatted string with the item details
        """
        if not self.valves.homebox_url:
            return "Error: Homebox API URL is required. Please set your Homebox API URL in the tool settings."
        
        # Ensure the URL has the correct format
        base_url = self.valves.homebox_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        endpoint = f"{base_url}/v1/items/{item_id}"
        
        try:
            response = requests.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            item = response.json()
            
            result = f"Item Details: {item['name']}\n\n"
            
            if 'description' in item and item['description']:
                result += f"Description: {item['description']}\n\n"
            
            # Basic information
            result += "Basic Information:\n"
            if 'assetId' in item and item['assetId']:
                result += f"- Asset ID: {item['assetId']}\n"
            
            if 'quantity' in item:
                result += f"- Quantity: {item['quantity']}\n"
            
            if 'manufacturer' in item and item['manufacturer']:
                result += f"- Manufacturer: {item['manufacturer']}\n"
            
            if 'modelNumber' in item and item['modelNumber']:
                result += f"- Model Number: {item['modelNumber']}\n"
            
            if 'serialNumber' in item and item['serialNumber']:
                result += f"- Serial Number: {item['serialNumber']}\n"
            
            # Location information
            if 'location' in item and item['location']:
                result += f"\nLocation: {item['location']['name']}\n"
            
            # Purchase information
            purchase_info = []
            if 'purchaseFrom' in item and item['purchaseFrom']:
                purchase_info.append(f"- Purchased From: {item['purchaseFrom']}")
            
            if 'purchasePrice' in item and item['purchasePrice']:
                purchase_info.append(f"- Purchase Price: {item['purchasePrice']}")
            
            if 'purchaseTime' in item and item['purchaseTime']:
                purchase_info.append(f"- Purchase Date: {item['purchaseTime']}")
            
            if purchase_info:
                result += "\nPurchase Information:\n" + "\n".join(purchase_info) + "\n"
            
            # Warranty information
            warranty_info = []
            if 'lifetimeWarranty' in item and item['lifetimeWarranty']:
                warranty_info.append("- Lifetime Warranty: Yes")
            
            if 'warrantyDetails' in item and item['warrantyDetails']:
                warranty_info.append(f"- Warranty Details: {item['warrantyDetails']}")
            
            if 'warrantyExpires' in item and item['warrantyExpires']:
                warranty_info.append(f"- Warranty Expires: {item['warrantyExpires']}")
            
            if warranty_info:
                result += "\nWarranty Information:\n" + "\n".join(warranty_info) + "\n"
            
            # Custom fields
            if 'fields' in item and item['fields']:
                result += "\nCustom Fields:\n"
                for field in item['fields']:
                    result += f"- {field['name']}: {field['value']}\n"
            
            # Notes
            if 'notes' in item and item['notes']:
                result += f"\nNotes:\n{item['notes']}\n"
            
            return result
        except requests.RequestException as e:
            return f"Error retrieving item details: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def list_locations(self) -> str:
        """
        List all locations in the homebox inventory.
        
        :return: A formatted string with the locations
        """
        if not self.valves.homebox_url:
            return "Error: Homebox API URL is required. Please set your Homebox API URL in the tool settings."
        
        # Ensure the URL has the correct format
        base_url = self.valves.homebox_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        endpoint = f"{base_url}/v1/locations"
        
        try:
            response = requests.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                result = f"Found {len(data['data'])} locations:\n\n"
                
                for idx, location in enumerate(data['data'], 1):
                    result += f"{idx}. {location['name']}\n"
                    if 'description' in location and location['description']:
                        result += f"   Description: {location['description']}\n"
                    result += f"   ID: {location['id']}\n\n"
                
                return result
            else:
                return "No locations found."
        except requests.RequestException as e:
            return f"Error listing locations: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def search_items_by_location(self, location_id: str, page: int = 1, page_size: int = 20) -> str:
        """
        Search for items in a specific location.
        
        :param location_id: The ID of the location to search in
        :param page: Page number (default: 1)
        :param page_size: Number of items per page (default: 20)
        :return: A formatted string with the search results
        """
        if not self.valves.homebox_url:
            return "Error: Homebox API URL is required. Please set your Homebox API URL in the tool settings."
        
        # Ensure the URL has the correct format
        base_url = self.valves.homebox_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        endpoint = f"{base_url}/v1/items"
        params = {
            "locations": [location_id],
            "page": page,
            "pageSize": page_size
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                # Get location name
                location_name = "Unknown Location"
                if len(data['data']) > 0 and 'location' in data['data'][0] and data['data'][0]['location']:
                    location_name = data['data'][0]['location']['name']
                
                result = f"Found {data['total']} items in location '{location_name}':\n\n"
                
                for idx, item in enumerate(data['data'], 1):
                    result += f"{idx}. {item['name']}\n"
                    
                    if 'description' in item and item['description']:
                        result += f"   Description: {item['description']}\n"
                    
                    if 'assetId' in item and item['assetId']:
                        result += f"   Asset ID: {item['assetId']}\n"
                    
                    if 'quantity' in item:
                        result += f"   Quantity: {item['quantity']}\n"
                    
                    result += "\n"
                
                # Add pagination info
                total_pages = (data['total'] + page_size - 1) // page_size
                result += f"Page {page} of {total_pages}\n"
                
                if page < total_pages:
                    result += f"Use 'page={page+1}' to see more results."
                
                return result
            else:
                return f"No items found in the specified location."
        except requests.RequestException as e:
            return f"Error searching items by location: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
