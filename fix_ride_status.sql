-- Fix Ride Status Bug
-- Convert all 'active' rides to 'scheduled'

-- First, let's see the current status distribution
SELECT status, COUNT(*) as count FROM rides GROUP BY status;

-- Update all 'active' rides to 'scheduled'
UPDATE rides SET status = 'scheduled' WHERE status = 'active';

-- Verify the update
SELECT status, COUNT(*) as count FROM rides GROUP BY status;

-- Check recent rides to confirm the fix
SELECT ride_id, origin, destination, status, created_at 
FROM rides 
WHERE created_at >= datetime('now', '-1 day')
ORDER BY created_at DESC;
