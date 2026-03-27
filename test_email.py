import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================================
# EMAIL CONFIGURATION
# ================================
MAIL_SERVER   = 'smtp.gmail.com'
MAIL_PORT     = 587
MAIL_USERNAME = 'campusconnect.noreplygmail@gmail.com'
MAIL_PASSWORD = 'fmgginvcvkjipcbk'

# ================================
# TEST EMAIL
# ================================
def test_email():
    print("=" * 50)
    print("CampusConnect - Email Test")
    print("=" * 50)

    try:
        print("\n[1] Creating email message...")
        msg            = MIMEMultipart('alternative')
        msg['Subject'] = 'CampusConnect - Email Test ✅'
        msg['From']    = MAIL_USERNAME
        msg['To']      = MAIL_USERNAME  # Sending to itself for testing

        text_body = """
        CampusConnect Email Test

        If you receive this email, your email
        configuration is working correctly!

        OTP system is ready to use.

        CampusConnect Team
        """

        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background:#f4f4f4; }
                .container {
                    max-width:500px; margin:30px auto;
                    background:white; border-radius:12px;
                    overflow:hidden;
                    box-shadow:0 4px 15px rgba(0,0,0,0.1);
                }
                .header {
                    background:linear-gradient(135deg,#1877f2,#0a5dc2);
                    color:white; padding:25px; text-align:center;
                }
                .body { padding:30px; text-align:center; }
                .success {
                    background:#ecfdf5; border:2px solid #a7f3d0;
                    border-radius:12px; padding:20px; margin:20px 0;
                }
                .success i { font-size:40px; }
                .footer {
                    background:#f8f9fa; padding:15px;
                    text-align:center; font-size:12px; color:#888;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 CampusConnect</h1>
                    <p>Email Configuration Test</p>
                </div>
                <div class="body">
                    <div class="success">
                        <p style="font-size:40px">✅</p>
                        <h2 style="color:#065f46">Email Working!</h2>
                        <p style="color:#666">
                            Your email configuration is
                            working correctly.
                            OTP emails will be sent successfully!
                        </p>
                    </div>
                    <p style="color:#666; font-size:14px">
                        This is a test email from CampusConnect.
                        Your Gmail SMTP is configured correctly.
                    </p>
                </div>
                <div class="footer">
                    © 2024 CampusConnect - COMSATS University Islamabad
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        print("[1] ✅ Email message created!")

        print("\n[2] Connecting to Gmail SMTP server...")
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=30)
        server.ehlo()
        print("[2] ✅ Connected to SMTP server!")

        print("\n[3] Starting TLS encryption...")
        server.starttls()
        server.ehlo()
        print("[3] ✅ TLS encryption started!")

        print("\n[4] Logging in to Gmail...")
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        print("[4] ✅ Login successful!")

        print("\n[5] Sending test email...")
        server.sendmail(MAIL_USERNAME, MAIL_USERNAME, msg.as_string())
        server.quit()
        print("[5] ✅ Email sent successfully!")

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print(f"\nCheck inbox of: {MAIL_USERNAME}")
        print("OTP system is ready to use!")

    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ AUTHENTICATION FAILED!")
        print(f"Error: {e}")
        print("\nPossible fixes:")
        print("1. Check Gmail address is correct")
        print("2. Check App Password is correct (no spaces)")
        print("3. Make sure 2FA is enabled on Gmail")
        print("4. Generate a new App Password")

    except smtplib.SMTPConnectError as e:
        print("\n❌ CONNECTION FAILED!")
        print(f"Error: {e}")
        print("\nPossible fixes:")
        print("1. Check your internet connection")
        print("2. Check MAIL_SERVER and MAIL_PORT")

    except smtplib.SMTPException as e:
        print("\n❌ SMTP ERROR!")
        print(f"Error: {e}")

    except Exception as e:
        print("\n❌ GENERAL ERROR!")
        print(f"Error: {e}")
        print(f"Error Type: {type(e).__name__}")

if __name__ == '__main__':
    test_email()