# Frankie Security Documentation

## Overview

Frankie implements comprehensive security controls to protect mortgage PII and ensure compliance with GLBA Safeguards Rule, ISO 27001, and NIST SP 800-53 standards.

## Security Standards Compliance

### GLBA Safeguards Rule
- ✅ **Administrative Safeguards**: Security officer, risk assessments, training
- ✅ **Technical Safeguards**: Encryption, access controls, monitoring
- ✅ **Physical Safeguards**: Physical access controls, secure disposal

### ISO 27001 Information Security Management
- ✅ **ISMS Framework**: Documented security policies and procedures
- ✅ **Risk Management**: Regular risk assessments and treatment
- ✅ **Access Control**: Role-based access control (RBAC)
- ✅ **Cryptography**: Encryption for data at rest and in transit

### NIST SP 800-53 Controls
- ✅ **Access Control (AC)**: Least privilege, session management
- ✅ **Audit and Accountability (AU)**: Comprehensive logging
- ✅ **Configuration Management (CM)**: Secure configurations
- ✅ **Identification and Authentication (IA)**: Multi-factor authentication
- ✅ **System and Communications Protection (SC)**: Encryption, secure channels

## Security Architecture

### Data Protection
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Backend API   │───▶│   Database      │
│   (HTTPS/TLS)   │    │   (Encrypted)   │    │   (Encrypted)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Session Mgmt  │    │   PII Encrypt   │    │   Audit Logs    │
│   (JWT)         │    │   (AES-256)     │    │   (Immutable)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Authentication Flow
1. **User Login**: Username/password with MFA
2. **Session Creation**: JWT token with expiration
3. **Access Control**: Role-based permissions
4. **Audit Logging**: All actions logged
5. **Session Management**: Automatic timeout

## Security Controls

### 1. Administrative Safeguards

#### Security Officer
- Appointed security officer responsible for compliance
- Regular security reviews and assessments
- Incident response coordination

#### Risk Assessments
- Quarterly security risk assessments
- Vulnerability scanning and penetration testing
- Third-party vendor security reviews

#### Employee Training
- Monthly security awareness training
- GLBA compliance training
- Incident response procedures

### 2. Technical Safeguards

#### Encryption
- **PII at Rest**: AES-256-GCM encryption
- **PII in Transit**: TLS 1.3 encryption
- **Key Management**: 90-day key rotation
- **Database**: Encrypted connections and storage

#### Authentication & Authorization
- **Multi-Factor Authentication**: Required for all users
- **Password Complexity**: 12+ characters, mixed case, numbers, symbols
- **Session Management**: 30-minute timeout
- **Account Lockout**: 5 failed attempts, 15-minute lockout

#### Access Control
- **Role-Based Access Control (RBAC)**:
  - Admin: Full system access
  - Broker: Read/write loan files
  - Processor: Read/write access
  - Viewer: Read-only access
- **Least Privilege**: Users only access necessary data
- **Session Validation**: Real-time session verification

#### Monitoring & Logging
- **Audit Logging**: All security events logged
- **Real-time Monitoring**: Suspicious activity detection
- **Log Retention**: 90 days minimum
- **Intrusion Detection**: Automated threat detection

### 3. Physical Safeguards

#### Office Security
- Restricted physical access to offices
- Secure disposal of documents and devices
- Hardware encryption for all devices
- Device management and tracking

### 4. Data Protection

#### PII Fields Encrypted
- Borrower information
- Broker information
- Social Security Numbers
- Email addresses
- Phone numbers
- Addresses
- Bank account information
- Credit card information
- Income information
- Employer information

#### Data Retention
- **Loan Files**: 7 years (GLBA requirement)
- **Email Communications**: 3 years
- **Audit Logs**: 7 years
- **Rate Data**: 2 years
- **Conversations**: 3 years

#### Data Classification
- **Public**: Non-sensitive information
- **Internal**: Business information
- **Confidential**: Loan application data
- **Restricted**: PII and financial data

## API Security

### Authentication
- JWT tokens for user authentication
- API keys for external integrations
- Rate limiting to prevent abuse
- Input validation and sanitization

### Security Headers
- HTTPS enforcement
- Secure cookie settings
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options

### CORS Policy
- Restricted to authorized domains
- No wildcard origins
- Secure credential handling

## Incident Response

### Response Plan
1. **Detection**: Automated monitoring and alerts
2. **Assessment**: Immediate threat assessment
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve

### Notification Timeline
- **Immediate**: Security team notification
- **1 Hour**: Management notification
- **24 Hours**: Regulatory notification (if required)
- **72 Hours**: Customer notification (if PII affected)

## Compliance Monitoring

### Regular Audits
- Quarterly security assessments
- Annual penetration testing
- Biannual security reviews
- Continuous compliance monitoring

### Security Metrics
- Failed login attempts
- Unauthorized access attempts
- Data access patterns
- System changes
- API usage anomalies

## Environment Variables

### Required for Production
```bash
JWT_SECRET_KEY=your-secure-jwt-secret
ENCRYPTION_KEY=your-encryption-key
DATABASE_URL=your-database-url
GMAIL_ADDON_API_KEY=your-gmail-api-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Optional
```bash
PASSWORD_SALT=your-password-salt
API_KEY_SALT=your-api-key-salt
VALID_API_KEYS=key1,key2,key3
SECURITY_LOG_LEVEL=INFO
```

## Security Best Practices

### For Developers
1. Never commit secrets to version control
2. Use environment variables for configuration
3. Validate all input data
4. Implement proper error handling
5. Follow secure coding practices

### For Users
1. Use strong, unique passwords
2. Enable multi-factor authentication
3. Report suspicious activity immediately
4. Log out when finished
5. Don't share credentials

### For Administrators
1. Regular security updates
2. Monitor audit logs
3. Review access permissions
4. Test incident response procedures
5. Conduct security training

## Security Contacts

### Security Officer
- Email: security@frankie.com
- Phone: (555) 123-4567
- Response Time: 24 hours

### Incident Response
- Emergency: (555) 911-0000
- Email: incidents@frankie.com
- Response Time: Immediate

### Compliance
- Email: compliance@frankie.com
- Phone: (555) 123-4568
- Response Time: 48 hours

## Security Updates

This document is reviewed and updated quarterly. Last updated: January 2025.

## Compliance Certifications

- GLBA Safeguards Rule: ✅ Compliant
- ISO 27001: 🔄 In Progress
- NIST SP 800-53: ✅ Aligned
- SOC 2 Type II: 🔄 Planned

## Security Resources

- [GLBA Safeguards Rule](https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act)
- [ISO 27001 Standard](https://www.iso.org/isoiec-27001-information-security.html)
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) 