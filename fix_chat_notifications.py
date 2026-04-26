#!/usr/bin/env python3
"""
Fix Chat Notifications for Both Driver and Passenger
Ensure both sides receive notifications when chat messages are sent
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def find_database():
    """Find the database file"""
    for possible_path in ['uniride.db', 'instance/uniride.db', 'data/uniride.db']:
        if Path(possible_path).exists():
            return possible_path
    return None

def backup_database(db_path):
    """Create a backup before making changes"""
    backup_path = f"{db_path}.backup_chat_notification_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def fix_passenger_chat_notifications():
    """Fix passenger chat notifications to work even when chat is closed"""
    print("\n🔧 Fixing Passenger Chat Notifications:")
    print("=" * 50)
    
    try:
        with open('templates/bookings.html', 'r') as f:
            content = f.read()
        
        # Check if the issue exists
        if "if (data.sender_id === currentDriverId || data.receiver_id === currentDriverId)" in content:
            print("🔍 Found issue: Passenger only receives notifications when chat is open")
            print("🔄 Fixing to show notifications even when chat is closed...")
            
            # Replace the new_message listener
            old_listener = """socket.on('new_message', (data) => {
            if (data.sender_id === currentDriverId || data.receiver_id === currentDriverId) {
                loadMessages(currentDriverId);
            }
        });"""
            
            new_listener = """socket.on('new_message', (data) => {
            // Always show notification for new messages
            showChatNotification(data);
            
            // If chat is open with this person, load messages
            if (currentDriverId && (data.sender_id === currentDriverId || data.receiver_id === currentDriverId)) {
                loadMessages(currentDriverId);
            }
        });
        
        // Show chat notification
        function showChatNotification(data) {
            // Don't show notification for own messages
            if (data.sender_id === {{ current_user.user_id }}) {
                return;
            }
            
            // Create notification element
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
            notification.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-comment-dots mr-2"></i>
                    <div>
                        <div class="font-semibold">New Message</div>
                        <div class="text-sm">${data.content.substring(0, 50)}${data.content.length > 50 ? '...' : ''}</div>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
            
            // Also show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('New Message', {
                    body: data.content,
                    icon: '/static/images/chat-icon.png'
                });
            }
        }"""
            
            fixed_content = content.replace(old_listener, new_listener)
            
            # Add notification permission request
            if 'requestNotificationPermission' not in fixed_content:
                fixed_content = fixed_content.replace(
                    'document.addEventListener(\'DOMContentLoaded\', function() {',
                    'document.addEventListener(\'DOMContentLoaded\', function() {\n        // Request notification permission\n        if (\'Notification\' in window && Notification.permission === \'default\') {\n            Notification.requestPermission();\n        }\n        '
                )
            
            with open('templates/bookings.html', 'w') as f:
                f.write(fixed_content)
            
            print("✅ Passenger chat notifications fixed")
        else:
            print("✅ Passenger chat notifications already fixed")
    
    except FileNotFoundError:
        print("❌ templates/bookings.html not found")
        return False
    
    return True

def fix_driver_chat_notifications():
    """Fix driver chat notifications to work even when chat is closed"""
    print("\n🔧 Fixing Driver Chat Notifications:")
    print("=" * 50)
    
    try:
        with open('templates/driver_dashboard.html', 'r') as f:
            content = f.read()
        
        # Check if the issue exists
        if "if (data.sender_id === currentPassengerId || data.receiver_id === currentPassengerId)" in content:
            print("🔍 Found issue: Driver only receives notifications when chat is open")
            print("🔄 Fixing to show notifications even when chat is closed...")
            
            # Replace the new_message listener
            old_listener = """socket.on('new_message', (data) => {
            if (data.sender_id === currentPassengerId || data.receiver_id === currentPassengerId) {
                loadMessages(currentPassengerId);
            }
        });"""
            
            new_listener = """socket.on('new_message', (data) => {
            // Always show notification for new messages
            showChatNotification(data);
            
            // If chat is open with this person, load messages
            if (currentPassengerId && (data.sender_id === currentPassengerId || data.receiver_id === currentPassengerId)) {
                loadMessages(currentPassengerId);
            }
        });
        
        // Show chat notification
        function showChatNotification(data) {
            // Don't show notification for own messages
            if (data.sender_id === {{ current_user.user_id }}) {
                return;
            }
            
            // Create notification element
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
            notification.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-comment-dots mr-2"></i>
                    <div>
                        <div class="font-semibold">New Message</div>
                        <div class="text-sm">${data.content.substring(0, 50)}${data.content.length > 50 ? '...' : ''}</div>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
            
            // Also show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('New Message', {
                    body: data.content,
                    icon: '/static/images/chat-icon.png'
                });
            }
        }"""
            
            fixed_content = content.replace(old_listener, new_listener)
            
            # Add notification permission request
            if 'requestNotificationPermission' not in fixed_content:
                fixed_content = fixed_content.replace(
                    'document.addEventListener(\'DOMContentLoaded\', function() {',
                    'document.addEventListener(\'DOMContentLoaded\', function() {\n        // Request notification permission\n        if (\'Notification\' in window && Notification.permission === \'default\') {\n            Notification.requestPermission();\n        }\n        '
                )
            
            with open('templates/driver_dashboard.html', 'w') as f:
                f.write(fixed_content)
            
            print("✅ Driver chat notifications fixed")
        else:
            print("✅ Driver chat notifications already fixed")
    
    except FileNotFoundError:
        print("❌ templates/driver_dashboard.html not found")
        return False
    
    return True

def enhance_socket_handlers():
    """Enhance socket handlers to include sender information"""
    print("\n🔧 Enhancing Socket Handlers:")
    print("=" * 50)
    
    try:
        with open('sockets/chat_socket.py', 'r') as f:
            content = f.read()
        
        # Check if we need to add sender name to the message
        if "'sender_id': current_user.user_id," in content and "'sender_name'" not in content:
            print("🔄 Adding sender name to message data...")
            
            # Enhance the emit to include sender name
            old_emit = """emit('new_message', {
            'sender_id': current_user.user_id,
            'receiver_id': receiver_id,
            'content': content,
            'sent_at': msg.sent_at.isoformat(),
            'is_read': False
        }, room=room)"""
            
            new_emit = """emit('new_message', {
            'sender_id': current_user.user_id,
            'sender_name': current_user.name,
            'receiver_id': receiver_id,
            'content': content,
            'sent_at': msg.sent_at.isoformat(),
            'is_read': False
        }, room=room)"""
            
            fixed_content = content.replace(old_emit, new_emit)
            
            with open('sockets/chat_socket.py', 'w') as f:
                f.write(fixed_content)
            
            print("✅ Socket handlers enhanced with sender name")
        else:
            print("✅ Socket handlers already enhanced")
    
    except FileNotFoundError:
        print("❌ sockets/chat_socket.py not found")
        return False
    
    return True

def create_notification_test():
    """Create a test function to verify notifications work"""
    print("\n🧪 Creating Notification Test:")
    print("=" * 50)
    
    test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Notification Test</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .notification { 
            position: fixed; top: 20px; right: 20px; 
            background: #007bff; color: white; 
            padding: 15px; border-radius: 8px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            max-width: 300px;
        }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Chat Notification Test</h1>
    <p>Open this page in two different browser windows to test notifications.</p>
    
    <button onclick="sendTestMessage()">Send Test Message</button>
    <button onclick="requestNotificationPermission()">Request Browser Notifications</button>
    
    <div id="status"></div>
    
    <script>
        let socket = io();
        let userId = Math.floor(Math.random() * 1000); // Random user ID for testing
        
        socket.on('connect', () => {
            document.getElementById('status').innerHTML = 'Connected as User ' + userId;
        });
        
        socket.on('new_message', (data) => {
            showNotification(data);
        });
        
        function sendTestMessage() {
            const receiverId = userId === 1 ? 2 : 1; // Alternate between user 1 and 2
            socket.emit('send_private_message', {
                receiver_id: receiverId,
                ride_id: 1,
                content: 'Test message from User ' + userId
            });
        }
        
        function showNotification(data) {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = `
                <strong>New Message from User ${data.sender_id}</strong><br>
                ${data.content}
                <button onclick="this.parentElement.remove()" style="float: right;">×</button>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
        
        function requestNotificationPermission() {
            if ('Notification' in window) {
                Notification.requestPermission().then(permission => {
                    alert('Notification permission: ' + permission);
                });
            }
        }
    </script>
</body>
</html>
    """
    
    with open('test_notifications.html', 'w') as f:
        f.write(test_html)
    
    print("✅ Created test_notifications.html for testing")
    return True

def main():
    print("🔧 Chat Notification Fix Tool")
    print("=" * 50)
    print("Fixing chat notifications to work for both driver and passenger")
    print("Both sides will now receive notifications even when chat is closed")
    
    # Find database
    db_path = find_database()
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Create backup
    if not backup_database(db_path):
        print("❌ Cannot proceed without backup!")
        return False
    
    # Apply fixes
    fix_passenger_chat_notifications()
    fix_driver_chat_notifications()
    enhance_socket_handlers()
    create_notification_test()
    
    print("\n✅ Chat Notification Fix Process Completed!")
    print("📋 What was fixed:")
    print("   1. Passengers now receive notifications even when chat is closed")
    print("   2. Drivers now receive notifications even when chat is closed")
    print("   3. Visual notifications appear on screen")
    print("   4. Browser notifications supported (with permission)")
    print("   5. Enhanced socket handlers with sender names")
    
    print("\n📋 Next steps:")
    print("   1. Restart the Flask application")
    print("   2. Open the application in two different browsers")
    print("   3. Test chat notifications between driver and passenger")
    print("   4. Check that notifications appear even when chat is closed")
    
    print("\n🧪 To test notifications:")
    print("   1. Open test_notifications.html in two browser windows")
    print("   2. Send messages between windows")
    print("   3. Verify notifications appear in both windows")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
