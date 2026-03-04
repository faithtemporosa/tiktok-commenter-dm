-- ============================================================================
-- TikTok Automation Bot - Supabase Schema
-- ============================================================================
-- Run this SQL in your Supabase project (SQL Editor)
-- Tables: comment_reports, dm_reports, post_reports, live_logs

-- ============================================================================
-- 1. COMMENT REPORTS TABLE
-- Stores all comments posted by the automation bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS comment_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    timestamp TEXT NOT NULL,
    profile TEXT NOT NULL,
    video_url TEXT,
    video_id TEXT,
    comment TEXT NOT NULL,
    sheet TEXT,
    screenshot TEXT,
    UNIQUE(timestamp, profile, video_id)
);

-- Add screenshot column if table already exists
ALTER TABLE comment_reports ADD COLUMN IF NOT EXISTS screenshot TEXT;

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_comment_reports_timestamp ON comment_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_comment_reports_profile ON comment_reports(profile);
CREATE INDEX IF NOT EXISTS idx_comment_reports_sheet ON comment_reports(sheet);

-- Enable Row Level Security (optional - for team access control)
ALTER TABLE comment_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations (adjust based on your needs)
CREATE POLICY "Allow all comment_reports access" ON comment_reports
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- 2. DM REPORTS TABLE
-- Stores all DMs sent by the automation bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS dm_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    timestamp TEXT NOT NULL,
    profile TEXT NOT NULL,
    username TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'sent',
    UNIQUE(timestamp, profile, username)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_dm_reports_timestamp ON dm_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dm_reports_profile ON dm_reports(profile);
CREATE INDEX IF NOT EXISTS idx_dm_reports_username ON dm_reports(username);

-- Enable Row Level Security
ALTER TABLE dm_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations
CREATE POLICY "Allow all dm_reports access" ON dm_reports
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- 3. POST REPORTS TABLE (REPOST)
-- Stores all reposts made by the automation bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS post_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    timestamp TEXT NOT NULL,
    profile TEXT NOT NULL,
    video TEXT,
    caption TEXT,
    status TEXT DEFAULT 'reposted',
    content_type TEXT,
    UNIQUE(timestamp, profile, video)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_post_reports_timestamp ON post_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_post_reports_profile ON post_reports(profile);
CREATE INDEX IF NOT EXISTS idx_post_reports_content_type ON post_reports(content_type);

-- Enable Row Level Security
ALTER TABLE post_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations
CREATE POLICY "Allow all post_reports access" ON post_reports
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- 4. LIVE LOGS TABLE
-- Stores real-time logs and status from the local bot
-- ============================================================================
CREATE TABLE IF NOT EXISTS live_logs (
    id UUID DEFAULT '00000000-0000-0000-0000-000000000001' PRIMARY KEY,
    logs JSONB DEFAULT '[]'::jsonb,
    status JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default row
INSERT INTO live_logs (id, logs, status) 
VALUES ('00000000-0000-0000-0000-000000000001', '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Enable Row Level Security
ALTER TABLE live_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations
CREATE POLICY "Allow all live_logs access" ON live_logs
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- Enable Realtime for all tables (for live dashboard updates)
-- ============================================================================
-- Go to Supabase Dashboard > Database > Replication and enable:
-- - comment_reports
-- - dm_reports
-- - post_reports
-- - live_logs

-- Or run these commands if available in your Supabase version:
-- ALTER PUBLICATION supabase_realtime ADD TABLE comment_reports;
-- ALTER PUBLICATION supabase_realtime ADD TABLE dm_reports;
-- ALTER PUBLICATION supabase_realtime ADD TABLE post_reports;
-- ALTER PUBLICATION supabase_realtime ADD TABLE live_logs;
