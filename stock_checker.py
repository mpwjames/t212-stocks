import requests
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json

def send_email(text, recipients):
    """Send email with the stock updates"""
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['EMAIL_PASSWORD']
    
    # Create the email content
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['Subject'] = 'New Stocks Added to Trading212'
    msg.attach(MIMEText(text, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()

def main():
    # API endpoint
    url = "https://demo.trading212.com/api/v0/equity/metadata/instruments"
    headers = {"Authorization": os.environ['T212_API_KEY']}

    # Get new data
    response = requests.get(url, headers=headers)
    print(f"API Response status code: {response.status_code}")

    if response.status_code == 200:
        # Process new data
        df_new = pd.DataFrame(response.json())
        df_new['date'] = pd.to_datetime(df_new['addedOn'], utc=True)

        # Read existing data
        try:
            df_current = pd.read_csv('t212_current.csv', index_col=[0])
            current_tickers = df_current['ticker'].to_list()
        except Exception as e:
            print(f"Error reading current CSV, assuming empty: {e}")
            current_tickers = []

        new_tickers = df_new['ticker'].to_list()
        new_unique_tickers = list(set(new_tickers) - set(current_tickers))

        if new_unique_tickers:
            # Filter and format new stocks
            filtered_rows = df_new[df_new['ticker'].isin(new_unique_tickers)]
            new_stocks = filtered_rows[['shortName', 'type', 'date']]
            new_stocks.columns = ['Name', 'type', 'date']

            # Format the date to the desired format
            new_stocks['date'] = new_stocks['date'].dt.strftime('%Y-%m-%d %H:%M')
            new_stocks = new_stocks.drop_duplicates(keep='first)

            # Create email content
            header = 'New stocks added to Trading212:\n\nName | Type | Date\n'
            rows = '\n'.join(f"{row['Name']} | {row['type']} | {row['date']}" 
                           for _, row in new_stocks.iterrows())
            text = header + rows
            print(text)

            # Save updated data
            df_new.to_csv('t212_current.csv')

            # Get recipients from environment variable
            recipients = json.loads(os.environ['RECIPIENTS'])
            
            # Send email
            send_email(text, recipients)
        else:
            print("No new stocks found")
    else:
        print(f"Error fetching data: {response.status_code}")

if __name__ == "__main__":
    main()
