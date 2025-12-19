# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **your.email@example.com**

Include the following information in your report:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Resolution Timeline**: We aim to resolve critical issues within 30 days
- **Disclosure**: We will coordinate with you on public disclosure timing

### Security Best Practices for Users

#### Protecting Your Credentials

1. **Never commit credentials to version control**
   - Use environment variables or `.env` files
   - Add `.env` to your `.gitignore`

2. **Use minimal API token permissions**
   - Create tokens specifically for this tool
   - Revoke tokens when no longer needed

3. **Rotate API tokens regularly**
   - Atlassian recommends rotating tokens periodically
   - Revoke old tokens after rotation

#### Safe Usage

```bash
# Good: Use environment variables
export CONFLUENCE_API_TOKEN="your-token"
confluence-export --pages 12345

# Good: Use .env file (not committed to git)
# .env file contents:
# CONFLUENCE_API_TOKEN=your-token

# Avoid: Passing token directly in command (may be visible in shell history)
confluence-export --token "your-token" --pages 12345
```

#### Securing Exported Content

- Exported files may contain sensitive information from your Confluence pages
- Store exports in secure locations with appropriate access controls
- Be cautious when sharing exported files
- Consider encrypting backups that contain sensitive data

## Security Considerations

### Data Handling

- This tool accesses your Confluence instance via the REST API
- Credentials are only used for API authentication and are not stored persistently
- Exported content is written to local files in your specified output directory

### Dependencies

We regularly update dependencies to address known vulnerabilities. The project uses:

- `requests` - HTTP library for API calls
- `beautifulsoup4` - HTML parsing
- `markdownify` - HTML to Markdown conversion
- `python-dotenv` - Environment variable management

### Network Security

- All communication with Confluence Cloud uses HTTPS
- API tokens are sent via HTTP Basic Authentication over TLS

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities (with their permission).

---

Thank you for helping keep Confluence Export CLI and its users safe!


