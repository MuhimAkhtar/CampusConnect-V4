import smtplib

EMAIL    = 'fa24-bse-080@isbstudent.comsats.edu.pk'
PASSWORD = '8101-249'

try:
    server = smtplib.SMTP('smtp.office365.com', 587, timeout=30)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(EMAIL, PASSWORD)
    print("SUCCESS! Outlook connected!")
    server.quit()
except Exception as e:
    print(f"FAILED! Error: {e}")