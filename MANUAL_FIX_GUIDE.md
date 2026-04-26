# 🔧 Manual Fix Guide for Both Issues

## Issue 1️⃣: Ride Status Bug

### Problem
New rides are being created with 'active' status instead of 'scheduled', causing them to not appear in search results.

### Root Cause
- Old rides in database still have 'active' status
- Search system looks for 'scheduled' or 'ongoing' rides
- 'active' rides don't match search criteria

### SQL Fix
```sql
-- Check current status distribution
SELECT status, COUNT(*) FROM rides GROUP BY status;

-- Fix: Convert all 'active' rides to 'scheduled'
UPDATE rides SET status = 'scheduled' WHERE status = 'active';

-- Verify the fix
SELECT status, COUNT(*) FROM rides GROUP BY status;

-- Check recent rides
SELECT ride_id, origin, destination, status, created_at 
FROM rides 
ORDER BY created_at DESC 
LIMIT 10;
```

### Expected Results
- All rides should have status: 'scheduled', 'ongoing', 'completed', or 'cancelled'
- No rides should have 'active' status
- New rides should appear in passenger search

---

## Issue 2️⃣: User Deletion Issues

### Problem
Users cannot be fully deleted due to foreign key relationships with dependent tables.

### Root Cause
- Users have related records in: rides, bookings, ratings, messages
- Foreign key constraints prevent deletion of users with dependent records
- Deletion must follow proper dependency order

### SQL Fix - Complete User Reset
```sql
-- Check current data
SELECT COUNT(*) as users FROM users;
SELECT COUNT(*) as rides FROM rides;
SELECT COUNT(*) as bookings FROM bookings;
SELECT COUNT(*) as ratings FROM ratings;
SELECT COUNT(*) as messages FROM messages;

-- Delete in correct order (respecting foreign keys)
DELETE FROM ratings;
DELETE FROM bookings;
DELETE FROM messages;
DELETE FROM rides;
DELETE FROM users;

-- Reset auto-increment IDs
DELETE FROM sqlite_sequence WHERE name IN ('users', 'rides', 'bookings', 'ratings', 'messages');

-- Verify deletion
SELECT COUNT(*) as users FROM users;
SELECT COUNT(*) as rides FROM rides;
SELECT COUNT(*) as bookings FROM bookings;
SELECT COUNT(*) as ratings FROM ratings;
SELECT COUNT(*) as messages FROM messages;
```

### SQL Fix - Create Sample Users (Optional)
```sql
INSERT INTO users (name, email, phone, role, password_hash, created_at) VALUES
('admin', 'admin@uniride.local', '+966500000001', 'admin', 'pbkdf2:sha256:260000$admin_salt$admin_hash', datetime('now')),
('driver1', 'driver1@uniride.local', '+966500000002', 'driver', 'pbkdf2:sha256:260000$driver1_salt$driver1_hash', datetime('now')),
('driver2', 'driver2@uniride.local', '+966500000003', 'driver', 'pbkdf2:sha256:260000$driver2_salt$driver2_hash', datetime('now')),
('passenger1', 'passenger1@uniride.local', '+966500000004', 'passenger', 'pbkdf2:sha256:260000$passenger1_salt$passenger1_hash', datetime('now')),
('passenger2', 'passenger2@uniride.local', '+966500000005', 'passenger', 'pbkdf2:sha256:260000$passenger2_salt$passenger2_hash', datetime('now'));

-- Verify sample users
SELECT user_id, name, email, role FROM users ORDER BY user_id;
```

---

## 🔍 Verification Steps

### After Ride Status Fix
1. **Check Status Distribution:**
   ```sql
   SELECT status, COUNT(*) FROM rides GROUP BY status;
   ```
   - Should show: scheduled, ongoing, completed, cancelled
   - Should NOT show: active

2. **Test Search Functionality:**
   - Create a new ride as driver
   - Search as passenger
   - Ride should appear in results

### After User Deletion Fix
1. **Check User Count:**
   ```sql
   SELECT COUNT(*) FROM users;
   ```
   - Should be 0 (or sample count if created)

2. **Check Dependent Tables:**
   ```sql
   SELECT COUNT(*) FROM rides;
   SELECT COUNT(*) FROM bookings;
   SELECT COUNT(*) FROM ratings;
   ```
   - Should all be 0

---

## 🚀 How to Execute

### Option 1: Use Python Script
```bash
python fix_both_issues.py
```

### Option 2: Manual SQL Execution
```bash
# Connect to database
sqlite3 instance/uniride.db

# Run SQL commands from this guide
```

### Option 3: SQL File
```bash
# Run ride status fix
sqlite3 instance/uniride.db < fix_ride_status.sql

# Run user deletion fix (create combined SQL file)
sqlite3 instance/uniride.db < complete_fix.sql
```

---

## ⚠️ Important Notes

### Backup First
Always create a backup before running fixes:
```bash
cp instance/uniride.db instance/uniride.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Foreign Key Order
The deletion order is critical:
1. **ratings** (depends on rides, users)
2. **bookings** (depends on rides, users)  
3. **messages** (depends on users)
4. **rides** (depends on users)
5. **users** (no dependencies)

### Status Flow
Correct ride status flow:
1. **Create** → `scheduled` ✅
2. **Start** → `ongoing` (driver action)
3. **Complete** → `completed` (driver action)
4. **Cancel** → `cancelled` (driver/admin action)

### Search Visibility
- **Visible:** `scheduled`, `ongoing`
- **Hidden:** `completed`, `cancelled`

---

## 🎯 Expected Final State

### Ride Status Fix
- ✅ No rides with 'active' status
- ✅ All new rides start as 'scheduled'
- ✅ Search functionality works correctly
- ✅ Driver can mark rides as completed

### User Deletion Fix
- ✅ All users deleted (or reset to sample data)
- ✅ No orphan records in dependent tables
- ✅ Auto-increment IDs reset
- ✅ Clean slate for new users

---

## 🆘 Troubleshooting

### If Rides Still Don't Appear
1. Check ride creation logic in `services/ride_service.py`
2. Verify search logic in `services/ride_service.py` (line 27-30)
3. Check frontend JavaScript for search parameters

### If User Deletion Fails
1. Check for additional foreign key constraints
2. Look for triggers that might prevent deletion
3. Verify all dependent tables are included in deletion order

### If Database Gets Corrupted
1. Restore from backup
2. Run fixes one at a time
3. Verify each step before proceeding

---

## 📞 Support

If issues persist:
1. Check application logs for errors
2. Verify database file permissions
3. Test with a small subset of data first
4. Contact support with specific error messages
