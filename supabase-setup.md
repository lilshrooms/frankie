# Supabase Setup for Frankie

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Choose your organization
5. Enter project details:
   - **Name**: `frankie-backend`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
6. Click "Create new project"

## Step 2: Get Connection Details

Once your project is created:

1. Go to **Settings** → **Database**
2. Copy the connection details:
   - **Host**: `db.xxxxxxxxxxxxx.supabase.co`
   - **Database name**: `postgres`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: (the one you set)

## Step 3: Update Environment Variables

Add these to your `.env` file:

```bash
# Supabase Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres

# Supabase API (for future features)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Step 4: Install PostgreSQL Dependencies

```bash
cd backend-broker
pip install psycopg2-binary
```

## Step 5: Run Database Migration

```bash
python migrate_to_supabase.py
```

## Step 6: Verify Connection

```bash
python test_supabase_connection.py
```

## Step 7: Update Gmail Add-on Configuration

Update `gmail-addon/config.js`:

```javascript
const CONFIG = {
  FRANKIE_API_BASE: 'https://your-production-domain.com', // Update for production
  FRANKIE_API_KEY: 'frankie-gmail-addon-key-2025',
  // ... rest of config
};
```

## Benefits of Supabase

✅ **Cloud-hosted PostgreSQL** - No local database management
✅ **Automatic backups** - Daily backups included
✅ **Real-time subscriptions** - Future feature for live updates
✅ **Row Level Security** - Built-in security features
✅ **Database dashboard** - Easy to view and manage data
✅ **API generation** - Auto-generated REST API
✅ **Scalability** - Handles growth automatically

## Next Steps

1. Deploy your backend to a cloud service (Railway, Heroku, etc.)
2. Update the Gmail Add-on to use the production URL
3. Set up environment variables in your production environment
4. Test the full integration 