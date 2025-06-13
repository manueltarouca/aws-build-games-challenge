"""
Highscore client for communicating with the web service
"""

import requests
import json
from typing import Dict, List, Optional
import threading
import time

class HighscoreClient:
    """Client for highscore web service"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 5  # seconds
        
    def submit_score(self, username: str, score: int, floor_reached: int, 
                    gold_collected: int, enemies_defeated: int) -> Dict:
        """Submit a score to the service"""
        try:
            data = {
                'username': username,
                'score': score,
                'floor_reached': floor_reached,
                'gold_collected': gold_collected,
                'enemies_defeated': enemies_defeated
            }
            
            print(f"🚀 Submitting score: {username} - {score} points")
            
            response = requests.post(
                f"{self.base_url}/api/submit_score",
                json=data,
                timeout=self.timeout
            )
            
            print(f"📡 Server response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Submission successful: {result}")
                return result
            else:
                error_msg = f'HTTP {response.status_code}'
                try:
                    error_detail = response.json().get('error', '')
                    if error_detail:
                        error_msg += f': {error_detail}'
                except:
                    pass
                print(f"❌ Submission failed: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f'Network error: {str(e)}'
            print(f"❌ Network error: {error_msg}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            print(f"❌ Unexpected error: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_highscores(self, limit: int = 10) -> Dict:
        """Get top highscores"""
        try:
            print(f"📊 Fetching top {limit} highscores...")
            
            response = requests.get(
                f"{self.base_url}/api/highscores",
                params={'limit': limit},
                timeout=self.timeout
            )
            
            print(f"📡 Highscores response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                score_count = len(result.get('scores', []))
                print(f"✅ Retrieved {score_count} highscores")
                return result
            else:
                error_msg = f'HTTP {response.status_code}'
                print(f"❌ Failed to get highscores: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f'Network error: {str(e)}'
            print(f"❌ Network error getting highscores: {error_msg}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            print(f"❌ Unexpected error getting highscores: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_user_rank(self, username: str) -> Dict:
        """Get user's rank and best score"""
        try:
            response = requests.get(
                f"{self.base_url}/api/user_rank",
                params={'username': username},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def get_stats(self) -> Dict:
        """Get general statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/api/stats",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def is_service_available(self) -> bool:
        """Check if the highscore service is available"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def submit_score_async(self, username: str, score: int, floor_reached: int,
                          gold_collected: int, enemies_defeated: int, 
                          callback=None):
        """Submit score asynchronously"""
        def submit():
            result = self.submit_score(username, score, floor_reached, 
                                     gold_collected, enemies_defeated)
            if callback:
                callback(result)
        
        thread = threading.Thread(target=submit, daemon=True)
        thread.start()

# Global instance
highscore_client = HighscoreClient()
