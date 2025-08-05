-- Create users table (handled by Supabase Auth)

-- Create spreadsheets table
CREATE TABLE IF NOT EXISTS spreadsheets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  sheets JSONB NOT NULL DEFAULT '[]',
  active_sheet_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create sharing table for collaboration
CREATE TABLE IF NOT EXISTS spreadsheet_shares (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  spreadsheet_id UUID REFERENCES spreadsheets(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  permission TEXT CHECK (permission IN ('read', 'write', 'admin')) DEFAULT 'read',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(spreadsheet_id, user_id)
);

-- Create RLS policies
ALTER TABLE spreadsheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE spreadsheet_shares ENABLE ROW LEVEL SECURITY;

-- Policies for spreadsheets
CREATE POLICY "Users can view their own spreadsheets" ON spreadsheets
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own spreadsheets" ON spreadsheets
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own spreadsheets" ON spreadsheets
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own spreadsheets" ON spreadsheets
  FOR DELETE USING (auth.uid() = user_id);

-- Policies for sharing
CREATE POLICY "Users can view shares for their spreadsheets" ON spreadsheet_shares
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM spreadsheets 
      WHERE spreadsheets.id = spreadsheet_shares.spreadsheet_id 
      AND spreadsheets.user_id = auth.uid()
    )
    OR auth.uid() = user_id
  );

CREATE POLICY "Users can create shares for their spreadsheets" ON spreadsheet_shares
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM spreadsheets 
      WHERE spreadsheets.id = spreadsheet_shares.spreadsheet_id 
      AND spreadsheets.user_id = auth.uid()
    )
  );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_spreadsheets_user_id ON spreadsheets(user_id);
CREATE INDEX IF NOT EXISTS idx_spreadsheet_shares_spreadsheet_id ON spreadsheet_shares(spreadsheet_id);
CREATE INDEX IF NOT EXISTS idx_spreadsheet_shares_user_id ON spreadsheet_shares(user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_spreadsheets_updated_at 
  BEFORE UPDATE ON spreadsheets 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
