# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the Telegram Temp Mail Bot deployment and testing.

## Workflow Files

### 1. `deploy.yml` - Main Deployment Workflow

**Triggers:**
- Push to `main` or `master` branch
- Manual workflow dispatch
- Daily schedule at 2 AM UTC (health monitoring)

**Jobs:**

#### `health-check`
- Lints code with flake8
- Checks code formatting with black
- Tests all Python imports
- Validates dependencies

#### `deploy`
- Deploys to production server via SSH
- Sets up Python virtual environment
- Installs system dependencies
- Configures environment variables
- Tests bot startup
- Handles deployment rollback on failure

#### `setup-service` (conditional)
- Creates systemd service file
- Enables automatic bot startup on server boot
- Only runs when commit message contains `[setup-service]`

#### `health-monitor` (scheduled)
- Runs daily for health monitoring
- Checks if bot service is running
- Tests MongoDB connectivity
- Monitors service logs for errors
- Auto-restarts bot if needed

#### `rollback` (failure handling)
- Automatically rolls back to previous version if deployment fails
- Restores from backup directory

### 2. `test.yml` - Testing and CI Workflow

**Triggers:**
- Push to any branch
- Pull requests to `main` or `master`

**Jobs:**

#### `lint`
- Python linting with flake8
- Code formatting check with black
- Import sorting check with isort

#### `import-test`
- Tests all Python module imports
- Validates external dependencies
- Checks for missing or broken imports

#### `config-test`
- Validates configuration module
- Tests environment file structure
- Checks required environment variables

#### `security`
- Security scan with Bandit
- Dependency vulnerability check with Safety
- Scans for hardcoded secrets

## Required GitHub Secrets

Add these secrets to your GitHub repository settings:

### Server Access
```
SERVER_HOST: Your server IP or hostname
SERVER_USERNAME: SSH username (e.g., ubuntu)
SERVER_SSH_KEY: Private SSH key content
SERVER_PORT: SSH port (default: 22)
APP_PATH: Application path on server (e.g., /home/user/apps)
```

### Application Configuration
```
TELEGRAM_BOT_TOKEN: Your Telegram bot token from @BotFather
MONGO_CONNECTION_STRING: MongoDB Atlas connection string
IMAP_HOST: IMAP server hostname
IMAP_PORT: IMAP server port (default: 993)
IMAP_USERNAME: IMAP server username
IMAP_PASSWORD: IMAP server password
EMAIL_DOMAIN: Email domain (default: seveton.site)
EMAIL_EXPIRY_HOURS: Email expiry time in hours (default: 1)
DEBUG_MODE: Debug mode flag (true/false)
LOG_LEVEL: Logging level (INFO, DEBUG, ERROR, etc.)
```

## Setup Instructions

### 1. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add all required secrets listed above

### 2. Server Preparation

On your deployment server:

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y python3 python3-pip python3-venv git libmagic1

# Create deployment user (optional)
sudo useradd -m -s /bin/bash botuser
sudo usermod -aG sudo botuser

# Create deployment directory
sudo mkdir -p /opt/botapps
sudo chown botuser:botuser /opt/botapps
```

### 3. Initial Setup (First Time)

Deploy with service setup:

```bash
git commit -m "Initial deployment [setup-service]"
git push origin main
```

### 4. Subsequent Deployments

Normal deployments (will update without changing service configuration):

```bash
git commit -m "Update bot features"
git push origin main
```

## Workflow Features

### ✅ Automated Deployment
- Zero-downtime deployment
- Automatic backup before deployment
- Rollback on failure
- Health checks after deployment

### ✅ Code Quality
- Automated linting
- Code formatting validation
- Import testing
- Security scanning

### ✅ Monitoring
- Daily health checks
- Service monitoring
- Error detection
- Automatic recovery

### ✅ Security
- Secure secret management
- Dependency vulnerability scanning
- Hardcoded secret detection
- SSH key authentication

## Troubleshooting

### Common Issues

**Deployment Fails:**
1. Check GitHub secrets are correctly configured
2. Verify server SSH access
3. Check server disk space
4. Review deployment logs in Actions tab

**Bot Won't Start:**
1. Check environment variables in .env file
2. Verify MongoDB connection string
3. Check IMAP server credentials
4. Review service logs: `sudo journalctl -u temp-mail-bot`

**Import Errors:**
1. Ensure all system dependencies are installed
2. Check Python version compatibility
3. Verify virtual environment setup

### Manual Commands

**Check service status:**
```bash
sudo systemctl status temp-mail-bot
```

**View service logs:**
```bash
sudo journalctl -u temp-mail-bot -f
```

**Restart service:**
```bash
sudo systemctl restart temp-mail-bot
```

**Manual deployment:**
```bash
cd /opt/botapps/TG
source venv/bin/activate
python bot.py
```

## Best Practices

1. **Test before deploying:** Use pull requests to test changes
2. **Monitor logs:** Regularly check service logs for issues
3. **Keep secrets secure:** Never commit secrets to repository
4. **Backup regularly:** Keep database and application backups
5. **Update dependencies:** Regularly update Python packages
6. **Security patches:** Apply system security updates promptly

## Maintenance

### Regular Tasks

1. **Monitor workflow runs:** Check Actions tab for failed runs
2. **Review security scans:** Address any security findings
3. **Update dependencies:** Update Python packages regularly
4. **Backup data:** Regular MongoDB backups
5. **Log rotation:** Configure log rotation for service logs

### Workflow Updates

To modify workflows:

1. Edit `.github/workflows/*.yml` files
2. Test changes in a feature branch
3. Create pull request for review
4. Merge to main after approval