import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_postgres import app, init_db

# Initialize DB on first cold start. 
# Note: Since Vercel is serverless, the /tmp database will be wiped when the function spins down.
# In a real production environment on Vercel, you should use an external database like Neon (Postgres) or Supabase.
init_db()

# Expose the Flask app as 'app' for the Vercel Python runtime
