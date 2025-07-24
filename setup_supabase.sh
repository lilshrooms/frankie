#!/bin/bash

# Frankie Supabase Setup Script
echo "🚀 Frankie Supabase Database Setup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "backend-broker/venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   cd backend-broker && python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source backend-broker/venv/bin/activate

# Check if psycopg2 is installed
if ! python -c "import psycopg2" 2>/dev/null; then
    echo "📦 Installing PostgreSQL dependencies..."
    pip install psycopg2-binary
fi

echo ""
echo "📋 Supabase Setup Instructions:"
echo "==============================="
echo ""
echo "1. 🌐 Go to https://supabase.com"
echo "2. 🔐 Sign up/Login with GitHub"
echo "3. ➕ Click 'New Project'"
echo "4. 📝 Enter project details:"
echo "   - Name: frankie-backend"
echo "   - Database Password: (generate a strong password)"
echo "   - Region: (choose closest to your users)"
echo "5. ✅ Click 'Create new project'"
echo ""
echo "6. 🔗 Get your connection details:"
echo "   - Go to Settings → Database"
echo "   - Copy the connection string"
echo ""
echo "7. 🔧 Set your DATABASE_URL:"
echo "   export DATABASE_URL='postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres'"
echo ""
echo "8. 🚀 Run the migration:"
echo "   cd backend-broker && python migrate_to_supabase.py"
echo ""
echo "9. 🧪 Test the connection:"
echo "   python test_supabase_connection.py"
echo ""
echo "📚 For detailed instructions, see: supabase-setup.md"
echo ""
echo "✨ Ready to migrate to Supabase!" 