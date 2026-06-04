"""
System testing script for SmartPark Backend
"""

import requests
import json
import time
from datetime import datetime, timedelta
import asyncio
import websockets

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test basic health endpoints"""
    print("🔍 Testing health endpoints...")
    
    try:
        # Root endpoint
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("✅ Root endpoint working")
        
        # Health check
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Health check: {data['status']}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def test_slots_api():
    """Test slots API endpoints"""
    print("\n🔍 Testing slots API...")
    
    try:
        # Get all slots
        response = requests.get(f"{BASE_URL}/api/slots")
        assert response.status_code == 200
        slots = response.json()
        print(f"✅ Retrieved {len(slots)} slots")
        
        if slots:
            slot_id = slots[0]["id"]
            
            # Get specific slot
            response = requests.get(f"{BASE_URL}/api/slots/{slot_id}")
            assert response.status_code == 200
            print(f"✅ Retrieved slot {slot_id}")
            
            # Get parking overview
            response = requests.get(f"{BASE_URL}/api/parking-overview")
            assert response.status_code == 200
            overview = response.json()
            print(f"✅ Parking overview: {overview['free_slots']}/{overview['total_slots']} free")
        
    except Exception as e:
        print(f"❌ Slots API test failed: {e}")

def test_reservations_api():
    """Test reservations API endpoints"""
    print("\n🔍 Testing reservations API...")
    
    try:
        # Get slots first
        response = requests.get(f"{BASE_URL}/api/slots")
        slots = response.json()
        
        if slots:
            slot_id = slots[0]["id"]
            
            # Create reservation
            start_time = datetime.now() + timedelta(hours=1)
            end_time = start_time + timedelta(hours=2)
            
            reservation_data = {
                "slot_id": slot_id,
                "user_id": 123,
                "user_name": "Test User",
                "user_email": "test@example.com",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            response = requests.post(
                f"{BASE_URL}/api/reservations",
                json=reservation_data
            )
            
            if response.status_code == 201:
                reservation = response.json()
                reservation_id = reservation["id"]
                print(f"✅ Created reservation {reservation_id}")
                
                # Get reservations
                response = requests.get(f"{BASE_URL}/api/reservations")
                assert response.status_code == 200
                reservations = response.json()
                print(f"✅ Retrieved {len(reservations)} reservations")
                
                # Cancel reservation
                response = requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel")
                if response.status_code == 200:
                    print("✅ Canceled reservation")
                
            else:
                print(f"⚠️ Could not create reservation: {response.text}")
        
    except Exception as e:
        print(f"❌ Reservations API test failed: {e}")

def test_forecast_api():
    """Test ML forecast API endpoints"""
    print("\n🔍 Testing forecast API...")
    
    try:
        # Get model info
        response = requests.get(f"{BASE_URL}/api/forecast/model-info")
        assert response.status_code == 200
        model_info = response.json()
        print(f"✅ Model info: {model_info['model_info']['is_trained']}")
        
        # Get forecast
        response = requests.get(f"{BASE_URL}/api/forecast?minutes=30")
        assert response.status_code == 200
        forecasts = response.json()
        print(f"✅ Generated {len(forecasts)} forecasts")
        
        # Get forecast summary
        response = requests.get(f"{BASE_URL}/api/forecast/summary?minutes=60")
        assert response.status_code == 200
        summary = response.json()
        print(f"✅ Forecast summary: {summary['summary']['likely_free']} likely free")
        
    except Exception as e:
        print(f"❌ Forecast API test failed: {e}")

def test_admin_api():
    """Test admin API endpoints"""
    print("\n🔍 Testing admin API...")
    
    try:
        # Get analytics
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 200
        analytics = response.json()
        print(f"✅ Analytics: {analytics['current_occupancy_rate']:.1f}% occupancy")
        
        # Get system logs
        response = requests.get(f"{BASE_URL}/api/admin/logs?limit=10")
        assert response.status_code == 200
        logs = response.json()
        print(f"✅ Retrieved {logs['total_logs']} system logs")
        
        # Get system status
        response = requests.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 200
        status = response.json()
        print(f"✅ System status: {status['overall_status']}")
        
    except Exception as e:
        print(f"❌ Admin API test failed: {e}")

async def test_websocket():
    """Test WebSocket connection"""
    print("\n🔍 Testing WebSocket connection...")
    
    try:
        uri = "ws://localhost:8000/ws/slots"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Send a test message
            await websocket.send("ping")
            
            # Wait for a short time to see if we get any messages
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"✅ Received WebSocket message: {message}")
            except asyncio.TimeoutError:
                print("✅ WebSocket connection stable (no immediate messages)")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

def test_ml_training():
    """Test ML model training"""
    print("\n🔍 Testing ML model training...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/forecast/train")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ML training: {result['message']}")
        else:
            print(f"⚠️ ML training response: {response.text}")
        
    except Exception as e:
        print(f"❌ ML training test failed: {e}")

def run_all_tests():
    """Run all system tests"""
    print("🚀 Starting SmartPark Backend System Tests")
    print("=" * 50)
    
    test_health_check()
    test_slots_api()
    test_reservations_api()
    test_forecast_api()
    test_admin_api()
    test_ml_training()
    
    # Run WebSocket test
    asyncio.run(test_websocket())
    
    print("\n" + "=" * 50)
    print("✅ System tests completed!")
    print("\n📋 Manual Tests to Perform:")
    print("1. Connect Arduino and verify serial communication")
    print("2. Test sensor state changes")
    print("3. Test servo motor commands")
    print("4. Monitor WebSocket updates in browser")
    print("5. Check database for logged events")

if __name__ == "__main__":
    run_all_tests()
