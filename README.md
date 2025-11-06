# Telegram Temp Mail Bot 📧

A fully functional Telegram bot that provides temporary email addresses with full IMAP inbox functionality, MongoDB integration, and attachment support.

## Features ✨

- 📧 **Generate temporary email addresses** at `@seveton.site`
- 📥 **Full IMAP inbox functionality** with real-time email fetching
- 📎 **Complete attachment support** (images, PDFs, documents, archives)
- 🔗 **MongoDB integration** for secure user data storage
- ⌨️ **Inline and reply keyboards** for easy navigation
- ⏰ **Auto-expiring emails** (configurable, default 1 hour)
- 🔄 **Background email fetching** with notifications
- 🛡️ **Secure IMAP connection** with SSL/TLS
- 📊 **User statistics and email management**
- 🎨 **Clean, responsive interface** with HTML formatting

## Quick Start 🚀

### Prerequisites

- Python 3.8+
- Telegram Bot Token
- MongoDB Atlas cluster
- IMAP server access (configured for `@seveton.site`)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TG
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Configure the bot**
   Edit `config.py` or set environment variables:
   ```python
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   MONGO_CONNECTION_STRING="mongodb+srv://..."
   IMAP_HOST="mail.seveton.site"
   IMAP_USERNAME="admin@seveton.site"
   IMAP_PASSWORD="your_imap_password"
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

## Configuration ⚙️

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# MongoDB
MONGO_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DATABASE_NAME=temp_mail_bot
MONGO_COLLECTION_NAME=users

# IMAP Server
IMAP_HOST=mail.seveton.site
IMAP_PORT=993
IMAP_USERNAME=admin@seveton.site
IMAP_PASSWORD=your_password
IMAP_USE_SSL=true

# Email Settings
EMAIL_DOMAIN=seveton.site
EMAIL_EXPIRY_HOURS=1

# Bot Settings
MAX_INBOX_MESSAGES=5
BACKGROUND_FETCH_INTERVAL=60
CLEANUP_INTERVAL=300
```

### Customization

You can customize various settings in `config.py`:

- Email expiry time
- Maximum inbox messages
- Background task intervals
- Attachment handling
- Rate limiting
- Logging levels

## Project Structure 📁

```
TG/
├── bot.py                    # Main bot application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── INSTALLATION.md           # Detailed installation guide
├── .env.example             # Environment variables template
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker Compose configuration
├── .github/workflows/        # GitHub Actions CI/CD workflows
│   ├── deploy.yml            # Main deployment workflow
│   ├── test.yml              # Testing and CI workflow
│   ├── docker.yml            # Docker build and deployment
│   └── README.md              # Workflow documentation
├── database/
│   └── mongo_client.py       # MongoDB operations
├── email_services/
│   ├── imap_client.py        # IMAP email fetching
│   ├── email_parser.py       # Email content parsing
│   └── email_generator.py    # Temporary email generation
├── handlers/
│   ├── command_handlers.py   # Telegram command handlers
│   ├── callback_handlers.py  # Inline button handlers
│   └── message_handlers.py   # Message and input handlers
├── keyboards/
│   ├── inline_keyboards.py   # Inline button layouts
│   └── reply_keyboards.py    # Reply keyboard layouts
└── utils/
    ├── validators.py         # Input validation utilities
    ├── formatters.py         # Message formatting utilities
    └── background_tasks.py   # Background processing
```

## Commands 🎯

### User Commands

- `/start` - Start bot and create temporary email
- `/new` - Generate new temporary email address
- `/inbox` - Show your email inbox
- `/refresh` - Check for new emails
- `/delete` - Delete your temporary email
- `/help` - Show help information
- `/status` - Show your email status

### Reply Keyboard Actions

- 📥 **Inbox** - Check your email inbox
- ✉️ **New Email** - Create new temporary email
- 🔁 **Refresh** - Refresh email list
- 🗑️ **Delete** - Delete temporary email

### Inline Buttons

- 📥 **Refresh Inbox** - Check for new emails
- ✉️ **New Email** - Generate new email address
- 🗑️ **Delete Temp Mail** - Remove current email
- 📧 **View Full Message** - View complete email
- 📎 **Download Attachments** - Get email attachments

## API Usage 🔌

### MongoDB Schema

User data is stored with the following structure:

```json
{
  "telegram_id": 123456789,
  "email": "prefix_random123@seveton.site",
  "prefix": "prefix",
  "created_at": "2025-01-01T12:00:00Z",
  "expires_at": "2025-01-01T13:00:00Z",
  "is_active": true,
  "last_checked": "2025-01-01T12:30:00Z",
  "message_count": 3,
  "total_messages_received": 5
}
```

### Email Generation Pattern

Email addresses follow this format:
- **Pattern**: `{prefix}_{random}@seveton.site`
- **Prefix**: 6 characters (user-defined or auto-generated)
- **Random**: 8 characters (alphanumeric)
- **Example**: `johnabc_x7k9m2p3@seveton.site`

## Deployment 🚀

### Local Development

1. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies and configure as above

3. Run locally:
   ```bash
   python bot.py
   ```

### Docker Deployment

1. **Using Docker Compose (Recommended)**:
   ```bash
   # Clone and configure
   git clone https://github.com/Lukerman/TG.git
   cd TG
   cp .env.example .env
   # Edit .env with your credentials

   # Run with Docker Compose
   docker-compose up -d
   ```

2. **Using Docker**:
   ```bash
   # Build image
   docker build -t temp-mail-bot .

   # Run container
   docker run -d \
     --name temp-mail-bot \
     --env-file .env \
     --restart unless-stopped \
     temp-mail-bot
   ```

3. **Multi-stage build**:
   ```bash
   # Build for production
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     -t temp-mail-bot:latest \
     --push .
   ```

### GitHub Actions CI/CD 🤖

The project includes comprehensive GitHub Actions workflows for automated deployment and testing:

**✅ Automated Workflows:**
- **CI Testing**: Linting, import testing, security scanning
- **Auto Deployment**: Zero-downtime deployment to production servers
- **Health Monitoring**: Daily health checks and automatic recovery
- **Container Deployment**: Docker image building and multi-architecture support
- **Rollback**: Automatic rollback on deployment failure

**📋 Required GitHub Secrets:**
```yaml
# Server Access
SERVER_HOST: your-server-ip
SERVER_USERNAME: ssh-username
SERVER_SSH_KEY: private-ssh-key
APP_PATH: /opt/botapps

# Application Configuration
TELEGRAM_BOT_TOKEN: your-telegram-token
MONGO_CONNECTION_STRING: mongodb-connection-string
IMAP_HOST: imap-server-host
IMAP_USERNAME: imap-username
IMAP_PASSWORD: imap-password
```

**🚀 Trigger Deployment:**
```bash
# Push to main branch (triggers auto-deployment)
git commit -m "Update bot features"
git push origin main

# Manual deployment
git commit -m "Deploy with service setup [setup-service]"
git push origin main
```

### VPS Deployment

1. **Set up server** (Ubuntu/Debian recommended):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Install bot**:
   ```bash
   git clone <repository-url>
   cd TG
   pip3 install -r requirements.txt
   ```

3. **Set up process manager** (systemd):
   ```ini
   # /etc/systemd/system/temp-mail-bot.service
   [Unit]
   Description=Telegram Temp Mail Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/path/to/TG
   ExecStart=/usr/bin/python3 bot.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/path/to/.env

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start service**:
   ```bash
   sudo systemctl start temp-mail-bot
   sudo systemctl enable temp-mail-bot
   ```

### Monitoring

- **Logs**: Bot logs are saved to `bot.log`
- **Health checks**: Built-in health monitoring
- **Statistics**: User and system statistics available
- **Error handling**: Comprehensive error reporting

## Security 🔒

### Data Protection

- IMAP connections use SSL/TLS encryption
- MongoDB connections use authentication
- No sensitive data is logged
- Temporary files are automatically cleaned up

### Input Validation

- All user inputs are validated and sanitized
- Email content is processed safely
- File attachments are scanned for safety
- Rate limiting prevents abuse

### Access Control

- Each user can only access their own emails
- MongoDB queries prevent data leakage
- Telegram user IDs are validated
- Proper session management

## Troubleshooting 🔧

### Common Issues

1. **IMAP Connection Failed**
   - Check IMAP server credentials
   - Verify SSL certificate
   - Check network connectivity

2. **MongoDB Connection Error**
   - Verify connection string
   - Check IP whitelist in MongoDB Atlas
   - Ensure correct database permissions

3. **Bot Token Invalid**
   - Verify bot token with @BotFather
   - Check for typos in token
   - Ensure bot is not running elsewhere

4. **Emails Not Appearing**
   - Check IMAP folder configuration
   - Verify email routing to the IMAP server
   - Check background task logs

### Debug Mode

Enable debug mode in `config.py`:
```python
DEBUG_MODE = True
```

This provides detailed logging and additional error information.

### Log Analysis

Check the bot log file:
```bash
tail -f bot.log
```

Common log entries to watch for:
- IMAP connection errors
- MongoDB query failures
- Telegram API rate limits
- Background task failures

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add proper error handling
- Include logging for debugging
- Update documentation
- Test thoroughly

## License 📄

This project is licensed under the MIT License. See LICENSE file for details.

## Support 💬

- 📧 **Issues**: Report bugs via GitHub Issues
- 📖 **Documentation**: Check this README and code comments
- 🔧 **Troubleshooting**: See Troubleshooting section
- 🤖 **Bot**: Start a conversation with the bot for help

## Changelog 📋

### Version 1.0.0
- Initial release
- Full IMAP email functionality
- MongoDB integration
- Attachment support
- Background email fetching
- Complete user interface
- Comprehensive error handling
- Security features
- Documentation

---

**Made with ❤️ for temporary email needs**