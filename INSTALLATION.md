# Installation Guide

## Quick Setup

### 1. Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (free tier works)
- Telegram Bot Token (from @BotFather)
- IMAP server access credentials

### 2. System Dependencies

Before installing Python packages, install these system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip libmagic1
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip file-devel
```

**macOS:**
```bash
brew install python3 libmagic
```

### 3. Clone and Install

```bash
# Clone the repository
git clone https://github.com/Lukerman/TG.git
cd TG

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
MONGO_CONNECTION_STRING=your_mongodb_connection_string
IMAP_HOST=your_imap_server
IMAP_PORT=993
IMAP_USERNAME=your_imap_username
IMAP_PASSWORD=your_imap_password
```

### 5. Run the Bot

```bash
python bot.py
```

## Troubleshooting

### Common Issues

**1. Import Error: No module named 'telegram'**
```bash
pip install python-telegram-bot
```

**2. Import Error: No module named 'magic'**
- Install system dependencies (see step 2)
- Reinstall python-magic: `pip uninstall python-magic && pip install python-magic`

**3. MongoDB Connection Error**
- Check connection string format
- Ensure IP whitelist includes your server IP
- Verify database user permissions

**4. IMAP Connection Error**
- Verify IMAP server credentials
- Check SSL certificate
- Test IMAP connection manually

### Testing Installation

Test that all imports work:
```bash
python -c "
import telegram
import motor
import magic
from dotenv import load_dotenv
print('✅ All dependencies installed successfully!')
"
```

## Production Deployment

For production deployment, consider:
- Using a process manager (systemd, supervisor)
- Setting up SSL certificates
- Configuring firewall rules
- Setting up monitoring and logging
- Using environment variables instead of .env file

## Need Help?

- Check the main README.md for detailed documentation
- Create an issue on GitHub for problems
- Review troubleshooting section in README.md