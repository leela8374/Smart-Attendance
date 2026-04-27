#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  deploy_ec2.sh – Run this on a fresh Amazon Linux 2023 /
#  Ubuntu 22.04 EC2 instance to install & start the app.
# ═══════════════════════════════════════════════════════════
set -e

APP_DIR="/home/ec2-user/smart-attendance"   # change for Ubuntu: /home/ubuntu/...
PYTHON="python3"

echo "────────────────────────────────────────"
echo " Smart Attendance – EC2 Bootstrap"
echo "────────────────────────────────────────"

# 1. System packages
sudo yum update -y  2>/dev/null || sudo apt-get update -y
sudo yum install -y python3 python3-pip git 2>/dev/null || \
  sudo apt-get install -y python3 python3-pip git

# 2. App directory
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# 3. Python venv
$PYTHON -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Set environment variables
#    (In production use AWS Systems Manager Parameter Store or Secrets Manager)
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export AWS_REGION="us-east-1"
export DYNAMO_USERS_TABLE="sas_users"
export DYNAMO_COURSES_TABLE="sas_courses"
export DYNAMO_ATTENDANCE_TABLE="sas_attendance"
export DYNAMO_ENROLLMENT_TABLE="sas_enrollment"
export SNS_TOPIC_ARN="YOUR_SNS_TOPIC_ARN_HERE"
export ATTENDANCE_THRESHOLD="75"

# 6. Create DynamoDB tables
echo "Setting up DynamoDB tables..."
python scripts/setup_dynamo.py

# 7. Seed initial data (first deploy only – remove for subsequent deploys)
echo "Seeding demo data..."
python scripts/seed_data.py

# 8. Start with Gunicorn (production WSGI server)
echo "Starting Gunicorn on port 5000..."
gunicorn --bind 0.0.0.0:5000 \
         --workers 3 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         "app:create_app()" &

echo ""
echo "✅ App running on http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
