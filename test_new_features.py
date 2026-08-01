#!/usr/bin/env python
"""Test new Phase 1 features: presets, analytics, sharing, premium, etc."""
import json
import sys
sys.path.insert(0, '/workspaces/dj-drop-factory-pro')

from app import app
from modules.database import Database

def test_features():
    db = Database()
    client = app.test_client()
    
    # Create test user
    reg_response = client.post('/api/auth/register', 
        json={'name': 'Test User', 'email': 'test@feature.com', 'password': 'pass123'})
    assert reg_response.status_code == 200
    reg_data = reg_response.get_json()
    token = reg_data['token']
    user_id = reg_data['user']['id']
    print("✅ User created:", user_id)
    
    # Test user profile update
    profile_response = client.post('/api/user/profile',
        headers={'Authorization': f'Bearer {token}'},
        json={'theme': 'dark', 'language': 'es'})
    assert profile_response.status_code == 200
    print("✅ Profile updated")
    
    # Test saving preset
    preset_response = client.post('/api/presets',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'Club Banger',
            'genre': 'club_banger',
            'voice': 'afro_vibe',
            'mood': 'energetic',
            'energy': 9,
            'fx_mode': 'standard'
        })
    assert preset_response.status_code == 200
    preset_data = preset_response.get_json()
    assert preset_data['success']
    print("✅ Preset saved:", preset_data.get('preset_id'))
    
    # Test fetching presets
    presets_response = client.get('/api/presets',
        headers={'Authorization': f'Bearer {token}'})
    assert presets_response.status_code == 200
    presets_data = presets_response.get_json()
    assert len(presets_data['presets']) > 0
    print("✅ Presets fetched:", len(presets_data['presets']))
    
    # Test logging prompt history
    history_response = client.post('/api/prompt-history',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'dj_name': 'DJ Test',
            'city': 'Lagos',
            'genre': 'afrobeat',
            'drop_type': 'intro',
            'mood': 'energetic',
            'energy': 8,
            'script': 'Welcome to the club!'
        })
    assert history_response.status_code == 200
    print("✅ Prompt history logged")
    
    # Test fetching prompt history
    hist_get_response = client.get('/api/prompt-history',
        headers={'Authorization': f'Bearer {token}'})
    assert hist_get_response.status_code == 200
    hist_data = hist_get_response.get_json()
    assert len(hist_data['history']) > 0
    print("✅ Prompt history fetched:", len(hist_data['history']))
    
    # Test analytics
    analytics_response = client.get('/api/analytics',
        headers={'Authorization': f'Bearer {token}'})
    assert analytics_response.status_code == 200
    analytics = analytics_response.get_json()
    assert analytics['success']
    print("✅ Analytics retrieved")
    
    # Test premium upgrade
    premium_response = client.post('/api/premium/upgrade',
        headers={'Authorization': f'Bearer {token}'})
    assert premium_response.status_code == 200
    assert premium_response.get_json()['success']
    print("✅ Premium upgraded")
    
    # Test share tracking
    share_response = client.post('/api/share',
        headers={'Authorization': f'Bearer {token}'},
        json={'platform': 'whatsapp', 'drop_id': 'test_drop'})
    assert share_response.status_code == 200
    print("✅ Share tracked")
    
    # Test Google sign-in
    google_response = client.post('/api/auth/google',
        json={'name': 'Google User', 'email': 'google@test.com'})
    assert google_response.status_code == 200
    google_data = google_response.get_json()
    assert google_data['success']
    print("✅ Google sign-in works")
    
    print("\n🎉 All Phase 1 features verified!")

if __name__ == '__main__':
    test_features()
